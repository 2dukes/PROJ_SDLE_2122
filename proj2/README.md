# Project 2
## Specification

This project explores the creation of a decentralized timeline service
(e.g. Twitter, Instagram, Facebook) that harvests peer-to-peer and edge de-
vices. Users have an identity and publish small text messages in their local
machine, forming a local timeline. They can subscribe to other user’s timelines
and will help to store and forward their content. Remote content is available
when a source or source subscriber is online and can forward the information.
Information from subscribed sources can be ephemeral and only stored and
forwarded for a given time period.

## Solution

The development of the project made us of `Kademlia` library from python, a Distributed Hash Table for decentralized P2P networks. This way, we managed each peer state using Kademlia's (key, value) pairs. Clock Synchronization between peers was done using the NTP Library. Direct communications between nodes that include, for example, follow/unfollow requests, are SSL encrypted to provide confidenciality to the system. Finally, an authentication system was implemented to enter the network.
## Install instructions:

`pip -r requirements.txt`

## Running the project:

> First, move to the `src/` folder by doing:

`cd src/`

Running nodes:

**Bootstrap node (1st node):**

`python3 menu/menu.py [-b | --bootstrap]`

**Other nodes:**

`python3 menu/menu.py`

