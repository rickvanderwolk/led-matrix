# Ntfy.sh

Use ntfy.sh to update the LED matrix in real time via WebSockets.

Build bar graphs, pixel creatures, or just see where your imagination takes you.

- [Getting started](#getting-started)
- [Update using curl](#update-using-curl)

<a id="getting-started"></a>
## Getting started 

Just publish a JSON message to a unique topic. No need to register or create any kind of tokens.

Just choose a unique topic, for example use a UUID generator.

⚠️ **Remember: this data is public — anyone who knows the topic can theoretically read this data and send updates to the LED matrix.**

Add this topic to the `config.json` file. 

For example:

```
{
  "selected_mode": "ntfy-sh",
  "ntfy-sh": {
    "topic": "90ad44f3b530"
  }
}
```

Replace `<your-ntfy-sh-topic>` with your topic in the examples below. 

For example:

```
curl -d '{"data": {"index": 0}}' https://ntfy.sh/90ad44f3b530
```

<a id="update-using-curl"></a>
## Update using curl

Update by index 

```
curl -d '{"data": {"index": 0}}' https://ntfy.sh/<your-ntfy-sh-topic>
```

Update by index with a specific color

```
curl -d '{"data": {"index": 5, "color": [0, 0, 255]}}' https://ntfy.sh/<your-ntfy-sh-topic>
```

Update multiple indexes with a specific color

```
curl -d '{
  "data": [
    {"index": 10, "color": [255, 0, 0]},
    {"index": 20, "color": [0, 255, 0]},
    {"index": 30, "color": [0, 0, 255]}
  ]
}' https://ntfy.sh/<your-ntfy-sh-topic>
```

Update using a pattern

```
curl -d '{
  "data": {
    "pattern": [1, 0, 1, 0, 1],
    "offset": 40,
    "color": [128, 0, 128]
  }
}' https://ntfy.sh/<your-ntfy-sh-topic>
```
Update using multiple patterns

```
curl -d '{
  "data": [
    {
      "pattern": [1, 0, 1],
      "offset": 0,
      "color": [255, 0, 0]
    },
    {
      "pattern": [1, 1, 0, 1],
      "offset": 10,
      "color": [0, 0, 255]
    }
  ]
}' https://ntfy.sh/<your-ntfy-sh-topic>
```

Combine update by index and update using a pattern

```
curl -d '{
  "color": [128, 128, 128],
  "data": [
    {
      "index": 5
    },
    {
      "pattern": [1, 0, 1],
      "offset": 20,
      "color": [0, 255, 0]
    },
    {
      "pattern": [0, 1, 1, 1],
      "offset": 40
    }
  ]
}' https://ntfy.sh/<your-ntfy-sh-topic>
```
