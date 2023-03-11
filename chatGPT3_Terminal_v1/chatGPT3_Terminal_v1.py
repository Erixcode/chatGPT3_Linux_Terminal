import openai
import os
import curses
import textwrap
import re
import datetime

def main():
    # Load OpenAI credentials from environment variables
    os.environ['OPENAI_API_KEY'] = 'OPENAI_APIKEY_HERE'
    openai.api_key = os.environ["OPENAI_API_KEY"]
    model_engine = "text-davinci-002"

    # Initialize variables
    command_mode = False
    history = []
    command_mode_message = "Command mode. Press 'i' to enter insert mode."

    # Set up curses
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
        curses.curs_set(0)

        # Define colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        text_color = curses.color_pair(1)
        you_color = curses.color_pair(2)
        chatgpt_color = curses.color_pair(3)

        # Define a function to generate responses
        def generate_response(prompt):
            completions = openai.Completion.create(
                engine=model_engine,
                prompt=prompt,
                max_tokens=150,
            )
            lines = []
            messages = [c.text.strip() for c in completions.choices]
            max_width = stdscr.getmaxyx()[1] - 10
            for message in messages:
                lines.extend(textwrap.wrap(f"chatGPT: {message}", max_width, subsequent_indent=" "*10))
                lines.append(("\n", 0))
            return lines[:-1]

        # Define a function to draw the screen
        def draw_screen(prompt, history, scroll_offset=0):
            rows, cols = stdscr.getmaxyx()
            stdscr.clear()

            # Determine the height and position of the scrollbar
            scrollbar_height = rows - 4
            if not history:
                max_history_size = 0
            else:
                max_history_size = max(0, len(history) - (rows - 4))
            if max_history_size == 0:
                scrollbar_pos = 0
            else:
                scrollbar_pos = min(scrollbar_height - 1, int((len(history)-max_history_size) / len(history) * scrollbar_height))

            # Calculate the top index based on the current scroll offset
            top_index = max(0, len(history) - rows + 4 - scroll_offset)
            if top_index > len(history):
                top_index = len(history)

            # Display chat history
            num_lines_displayed = 0
            for i, line in enumerate(history[top_index:]):
                line = str(line)  # Convert to string
                if num_lines_displayed < rows-4:  # Only display lines that fit on the screen
                    if line.startswith("You:"):
                        stdscr.addnstr(num_lines_displayed, 0, line, cols - 1, you_color)
                    elif line.startswith("chatGPT:"):
                        stdscr.addnstr(num_lines_displayed, 0, line, cols - 1, chatgpt_color)
                    else:
                        stdscr.addnstr(num_lines_displayed, 0, line, cols - 1)
                    num_lines_displayed += 1
                else:
                    break

            # Draw the scrollbar and prompt
            for i in range(scrollbar_height):
                char = "▓" if i == scrollbar_pos else "░"
                stdscr.addstr(i, cols-1, char, text_color)

            prompt_display = ">" + prompt.ljust(cols-1)
            stdscr.addstr(rows-2, 0, prompt_display, text_color)
            stdscr.addstr(rows-1, 0, command_mode_message if command_mode else "", text_color)

            # Move cursor to end of prompt
            stdscr.move(rows-2, min(len(prompt_display), cols-1))
            
            stdscr.refresh()

        # Enter main loop
        prompt = ""
        draw_screen(prompt, history)
        scroll_offset = 0
        while True:
            # Get user input
            c = stdscr.getch()

            # Handle arrow key input
            if c == curses.KEY_UP:
                scroll_offset += 1
                draw_screen(prompt, history, scroll_offset)
                continue
            elif c == curses.KEY_DOWN:
                scroll_offset -= 1
                if scroll_offset < 0:
                    scroll_offset = 0
                draw_screen(prompt, history, scroll_offset)
                continue

            # Handle other user input
            if c == 27:
                command_mode = not command_mode
                command_mode_message = "Command mode. Press 'i' to enter insert mode, 's' to save chat, 'q' to quit"
            elif command_mode:
                if c == ord('i'):
                    command_mode = False
                    prompt = ""
                elif c == ord(':'):
                    prompt = ":"
                elif c == ord('q'):
                    break
                elif c == ord('l'):
                    stdscr.erase()
                elif c == ord('s'):
                    now = datetime.datetime.now()
                    filename = f"chat-log-{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
                    with open(filename, 'w') as f:
                        for line in history:
                            f.write(line + "\n")
                    prompt = ""

            else:
                if c == curses.KEY_BACKSPACE or c == 127:
                    prompt = prompt[:-1]
                elif c == ord('\n'):
                    response = generate_response(prompt)
                    history.append(f'You: {prompt}\n')
                    for line in response:
                        line = re.sub('[^\x00-\x7F]+', '', line)  # Remove non-ASCII characters
                        history.append(line)
                    prompt = ""
                else:
                    prompt += chr(c)

            draw_screen(prompt, history, scroll_offset)

    except Exception as e:
        # Print any exception that occurred and exit
        curses.endwin()
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        exit()

    finally:
        # Clean up curses
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()


if __name__ == '__main__':
    main()

