# TODO for chatbot

-   [ ] figure out how to connect to the twitch API
-   [ ] assing a random color to a colourless user and store that forever and ever in the db so that we can bring back up
-   [ ] some way of keeping track of !drop results.
-   [ ] keep track of commands that people tried to use but were not implemented in the bot.
-   [ ] show the badges on the terminal version of the chat.
-   [ ] Figure out why `pyright` is complaing that the following dict:

    ```python
    AVAILABLE_COMMANDS: Dict[str, BaseCommand] = {
    		"hello": SayHelloCommand,  #type: ignore
    		"commands": ListCommandsCommand,
    		"today": TodayCommand,
    		"settoday": SetTodayCommand,
    }
    ```

    is imcompatible with the type hint when all of the classes it holds are in fact of type `BaseCommand`

-   [ ] look into why pyright complains that `BaseCommand` is not callable.
