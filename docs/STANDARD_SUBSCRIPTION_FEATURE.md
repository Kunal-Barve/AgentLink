# Standard Subscription Feature - Parked

## Status: **DISABLED** (Parked for future use)

## Overview
The standard subscription feature has been parked to save Make.com credits. This feature was costing approximately **60,000 credits** per run by making webhook calls to check if non-featured agents have standard subscriptions.

## How to Enable/Disable

### Currently Disabled (Default)
```
ENABLE_STANDARD_SUBSCRIPTION=false
```

### To Re-enable (If client requests it)
Change in `.env` file:
```
ENABLE_STANDARD_SUBSCRIPTION=true
```

## Technical Details

### Affected Files
1. **`.env`** - Feature flag configuration
2. **`app/services/domain_utils.py`** - `check_standard_subscription()` function
3. **`app/services/domain_service.py`** - Calls to check_standard_subscription()

### Webhook URL (Not called when disabled)
```
https://hook.eu2.make.com/gne36wgwoje49c54gwrz8lnf749mxw3e
```

### How It Works

#### When DISABLED (Current State):
- `check_standard_subscription()` returns `False` immediately without making any API calls
- All agents will have `standard_subscription=False`
- **No Make.com credits are consumed**
- Logs message: "Standard subscription feature is DISABLED"

#### When ENABLED:
- Makes POST request to webhook for each non-featured agent
- Sends: `{agent_name, suburb, state}`
- Receives: Boolean indicating subscription status
- Uses caching to avoid duplicate calls for same agent
- Logs subscription status for each agent

### Code Flow

1. **Domain Service** loops through all agents
2. Skips **featured agents** (they already have highest priority)
3. Checks cache first to avoid duplicate API calls
4. Calls `check_standard_subscription()` for each non-featured agent
5. **If feature is disabled**: Returns `False` immediately (no webhook call)
6. **If feature is enabled**: Makes webhook call and returns actual status

## Behavior When Disabled

- ✅ No webhook calls to Make.com
- ✅ Saves ~60K Make.com credits
- ✅ All agent processing continues normally
- ✅ All agents have `standard_subscription=False`
- ✅ Featured and Featured Plus agents still work normally
- ✅ Code remains intact for future re-enablement

## Re-enabling Instructions

If client wants the feature back:

1. Open `.env` file
2. Change `ENABLE_STANDARD_SUBSCRIPTION=false` to `ENABLE_STANDARD_SUBSCRIPTION=true`
3. Restart the application
4. Feature will immediately start making webhook calls again

## Notes

- Featured Plus agents have the highest priority
- Featured agents have second priority
- Standard subscription agents (when enabled) have third priority
- Regular agents have no priority

## Cost Savings

- **Before**: ~60,000 Make.com credits per full run
- **After**: 0 credits for standard subscription checks
- **Featured agents**: Still use credits (different webhook)
