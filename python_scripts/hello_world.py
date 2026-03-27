#!/usr/bin/python3
# @time_trigger("cron(0,30 * * * * *)")
def hello_world_2():
    #    print("Hello world!")
    #    logger.info("hello world")
    # `data` is available as builtin and is a dictionary with the input data.
    # name = data.get("name", "world")
    # `logger` and `time` are available as builtin without the need of explicit import.
    logger.info("Hello {} at {}".format(name, time.time()))


hello_world_2()
