# Project 1

This project aims to build a reliable publish-subscribe service.

It is made up of 3 programs:
- subscriber
- publisher
- proxy

The proxy program can be run using the following command (from the root of the project):

`$ python3 src/proxy.py`

The subscriber program has the following usage:

`$ python3 src/subscriber.py -i <id number> -f <path to config file>`

The publisher program has the following usage:

`$ python3 src/publisher.py -i <id number> -f <path to config file>`

The configuration files (yml files) are in the config folder, in the respective folder (publisher or subscriber), and have the goal of automating the usage of the subscribe and publish programs.

The configuration files for the publisher program have this structure:

```
steps:
  - topic: <topic name>
    message: <message content>
    number_of_times: <number of times to send the same message>
    sleep_between_messages: <number of seconds to sleep between sending each message>
    sleep_after: <number of seconds to sleep after sending all messages>

```

Additional steps can be added in order to send different messages. Now, let's look at an example:

```
steps:
  - topic: topic1
    message: Topic1 Msg
    number_of_times: 3
    sleep_between_messages: 1
    sleep_after: 5
  - topic: topic2
    message: Topic2 Msg
    number_of_times: 5
    sleep_between_messages: 1
    sleep_after: 1
```

With this configuration the publisher will publish the message "Topic1 Msg" 3 times (each time it will add "_<sequential number>" at the end to help distinguish each message) to the "topic1" topic, it will sleep for 1 second between sending messages and will sleep for 5 seconds after doing all this.
On the second step it will publish the message "Topic2 Msg" to the "topic2" topic 5 times (each time it will add "_<sequential number>" at the end to help distinguish each message), it will sleep for 1 second between sending messages and will sleep for 1 second once it's done.

The configuration files for the subscriber program have this structure:

```
steps:
  - action: subscribe
    topic: <topic name>
    sleep_after: <number of seconds to sleep after subscribing>
  - action: get
    topic: <topic name>
    number_of_times: <number of times to get a message from the topic>
    sleep_between: <number of seconds to sleep between each get>
    sleep_after: <number of seconds to sleep after all get operations>
  - action: unsubscribe
    topic: <topic name>
    sleep_after: <number of seconds to sleep after unsubscribing>
```

While this structure shows the steps in the order that you would expect them to be performed normally, you can change the order of the steps and even remove some of them.
For example, if you wanted to try to get messages from a topic without being subscribed to it, you could remove the first step or place it after the second one.
Let's look at another example:

```
steps:
  - action: subscribe
    topic: topic1
    sleep_after: 1
  - action: get
    topic: topic1
    number_of_times: 3
    sleep_between: 3
    sleep_after: 2
  - action: unsubscribe
    topic: topic1
    sleep_after: 2
```

In this example the subscriber program will first subscribe to the "topic1" topic and will sleep for 1 second after doing that.
In the next step it will perform the get operation for topic "topic1" 3 times, while sleeping for 3 seconds between each operation and after those, it will sleep for 2 seconds.
Finally, it will unsubscribe from the topic "topic1" and sleep for 2 seconds after that.

We also have a clean.sh file in the root of the project were backups for publishers, subscribers and/or proxy can be deleted.

Clean backup of publisher with ID `<PUBLISHER_ID>` and subscriber with ID `<SUBSCRIBER_ID>`:

`./clean.sh -p <PUBLISHER_ID> -s <SUBSCRIBER_ID>`

Clean backup of all publishers and subscribers:

`./clean.sh -P -S`

Clean backup of proxy:

`./clean.sh -X`

Clean backups of publishers, subscribers and proxy:

`./clean.sh -P -S -X`

Helper:

`./clean.sh -h`

Notice that if flag `-P` is provided, it doesn't make sense to also provide flags `-p` `<PUBLISHER_ID>`.
The same is valid for flag `-S`. It wouldn't also make sense to provide the flag `-s` `<SUBSCRIBER_ID>`.