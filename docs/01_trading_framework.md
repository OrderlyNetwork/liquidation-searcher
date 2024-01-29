# Trading Framework

## Why use a trading framework?

A trading bot is complicated or will be complicated. It needs to connect to exchanges, subscribe to market data, place orders, handle errors, etc. You will find yourself always need to add some extra checks or conditions. The code may be concise at the beginning but will soon become hard to maintain or slow to run. A trading framework can help you focus on your trading strategy and make your bot more robust.

## Why another trading framework?

I have read several trading frameworks in the Python world, but none of them is suitable for my needs. Some are too complicated including history data processing, backtesting, ML which a simple bot doesn't need. Some are too old, not supporting async/await, type hints, etc. Some are too simple, not supporting multiple exchanges, etc. So I decided to write my own trading framework.

## Design Principles

* Meet the YAGNI(You Aren’t Gonna Need It) principle.
* Should be modular, components should be clearly and distinctly delineated.
* Should be async and low latency.
* Should be event-driven and process real-time events.

The trading framework is heavily inspired by [paradigmxyz/artemis](https://github.com/paradigmxyz/artemis). So it's designed to be simple, modular and fast.

## Architecture

![trading_framework_arch](/assets/trading_framework_arch.png)

### Collectors

Collectors take in external events(such as from rest api or websocket) and turn them into an internal event representation(Attached an `event_type` field to distinguish with each other), and send it to the event queue.

A trading bot can contain many collectors, and they are run in parallel.

### Strategies

Strategies contain the core logic of the trading bot, which should be the most complicated part of your bot. Strategies take in internal events as inputs and compute whether any opportunities exist. If so, it will generate an action and send it to the action queue.

A trading bot can contain many strategies, and they are run in parallel.

### Executors

Executors take in actions and execute them. For example, if the action is to place an order, the executor will place the order to the exchange. If the action is to cancel an order, the executor will cancel the order. If the action is to send a notification, the executor will send the notification.

A trading bot can contain many executors, and they are run in parallel.

### Engine

The engine is the glue that connects all the components together. It takes in events from the event queue, and dispatches them to the corresponding strategies. It also takes in actions from the action queue, and dispatches them to the corresponding executors.

### Queues

Queues in the trading framework are broadcast queues(for first version, the events are handled one by one, will be changed to fully parallel in the future version)

* Event queue: collectors push collected events to the single event queue in the engine, and strategies consume them.
* Action queue: strategies push generated actions to the single action queue in the engine, and executors consume them.
