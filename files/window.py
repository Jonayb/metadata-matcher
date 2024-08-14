import PySimpleGUI as sg
from main import main_process


def create_main_window():
    """
    Creates the main window layout and returns the window object.
    """
    sg.theme("SandyBeach")

    layout = [
        [sg.Text('Enter suffix used for edited photos (optional):')],
        [sg.InputText(key='-INPUT_TEXT-'), sg.Button('Help')],
        [sg.Text("Choose a folder:")],
        [sg.Input(key="-IN2-", enable_events=True), sg.FolderBrowse()],
        [sg.Button("Match", size=(10, 1))],
        [sg.ProgressBar(100, visible=False, orientation='h', size=(30, 20), key='-PROGRESS_BAR-')],
        [sg.Text("", size=(40, 1), key='-PROGRESS_LABEL-', justification='center')]
    ]

    return sg.Window('Google Photos Matcher', layout, icon='photos.ico', finalize=True)


def main():
    """
    The main event loop for the application.
    """
    window = create_main_window()

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit"):
            break
        elif event == "Match":
            main_process(values["-IN2-"], window, values['-INPUT_TEXT-'])
        elif event == "Help":
            sg.Popup(
                "Media edited with the integrated editor of Google Photos will download both the original image 'Example.jpg' "
                "and the edited version 'Example-editado.jpg'. The 'editado' suffix changes depending on the language "
                "(e.g., 'editado' for Spanish). If you leave this box blank, the default Spanish suffix will be used.",
                title="Information",
                icon='photos.ico'
            )

    window.close()


if __name__ == "__main__":
    main()
