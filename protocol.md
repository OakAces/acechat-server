#Protocol Definition

## Overview

### Client Actions

Clients will send messages to the server in the following format:

```
{
  "command": "COMMANDNAME",
  "args": ["arg1", "arg2"]
}
```

### Server Actions

 Clients will receive messages from the server in the following
 format:

```
{
  "user": "username",
  "command": "COMMANDNAME",
  "args": ["arg1", "arg2"],
  "timestamp": 1326439500 // Unix Timestamp
}
```

## WebSocket Protocol Definition

### Client Actions

#### Message Actions

##### MSG - Send Message

```
{
  "command": "MSG",
  "args": ["channel", "message text goes here"]
}
```

##### PRIVMSG - Send Private Message

```
{
  "command": "PRIVMSG",
  "args": ["user", "message text"]
}
```

#### Channel Actions

##### JOIN - Join Channel

```
{
  "command": "JOIN",
  "args": ["channel1", "channel2"] // any number of channels
}
```

##### PART - Leave Channel

```
{
  "command": "PART",
  "args": ["channel1", "channel2"]
}

```

##### INVITE - Invite User to Channel

```
{
  "command": "INVITE",
  "args": ["channel", "user1", "user2"] // any number of users
}
```

##### CHANLIST - List Channels on Server

```
{
  "command": "CHANLIST",
  "args": []
}

```
#### User Actions

##### USER - Set Username

```
{
  "command": "USER",
  "args": ["username"]
}
```

##### USERLIST - List Users on Server
```
{
  "command": "USERLIST",
  "args": []
}
```
### Server Actions

#### Message Actions

##### MSG - Receive Message From a Channel
```
{
  "user": "username",
  "command": "MSG",
  "args": ["channel", "message text goes here"]
  "timestamp": 1326439500 // Unix Timestamp
}
```

##### PRIVMSG - Receive Message From User
```
{
  "user": "username",
  "command": "PRIVMSG",
  "args" ["user", "message text"]
  "timestamp": 1326439500 // unix timestamp
}
```
#### Channel Actions

##### JOIN - Someone Joined the Channel

```
{
  "user": "anthony",
  "command": "JOIN",
  // channel name and list of users
  "args": ["channel", "user1", "user2"], 
  "timestamp": 1326439500 // Unix Timestamp
}
```

##### PART - Someone Left the Channel

```
{
  "user": "username",
  "command": "PART",
  // channel name and list of users
  "args": ["channel", "user1", "user2"],
  "timestamp": 1326439500 // Unix Timestamp
}

```
##### CHANLIST - Enumerate Channels on Server
```
{
  "user": "",
  "command": "CHANLIST",
  "args": ["chan1", "chan2"] // all channels on server
  "timestamp": 1326439500 // Unix Timestamp
}
```

#### USER Actions

```
{
  "user": "",
  "command": "USERLIST",
  "args": ["user1", "user2"] // all users on server
  "timestamp": 1326439500 // Unix Timestamp
}
```

#### ERROR
```
{
  "command": "ERROR",
  "args": ["error text"]
}
```
