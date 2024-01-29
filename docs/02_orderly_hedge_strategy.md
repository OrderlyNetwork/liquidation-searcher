# Orderly Hedge Strategy

## Short Description

The bot is designed to watch the real-time liquidation events from Orderly Rest API and Websocket interface, and then claim a small portion of the liquidation position to gain the attached liquidator fee, and immediately create a reduce-only position to hedge the risk of the liquidation position.

## Collectors

* [orderly_liquidation_rest.py](/src/liquidation_searcher/collectors/orderly_liquidation_rest.py) - Collect liquidation events from Orderly Rest API. It can get existing liquidations.
* [orderly_liquidation_ws.py](/src/liquidation_searcher/collectors/orderly_liquidation_ws.py) - Collect liquidation events from Orderly Websocket interface. The Websocket data are only pushed on changes.

## Strategies

* [orderly_hedge.py](src/liquidation_searcher/strategies/orderly_hedge.py) - The strategy to hedge the liquidation position. It will deduplicate the liquidation IDs from rest and websocket APIs, and unify the liquidation event format and the trigger the order action.

## Executors

* [orderly_executor.py](src/liquidation_searcher/executors/orderly_executor.py) - Claim a small portion of the liquidation position and wait for the claim transfer finished, and lastly create a reduce-only position to hedge the risk of the liquidation position.
