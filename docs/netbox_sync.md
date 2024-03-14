## Usage

Once the organization has set up service federation for their netbox instance
the following command can be used to run the netbox sync job.

```python
Ctl/dev/run.sh ixctl_netbox_sync $ORG_SLUG $IX_SLUG
```

- `$ORG_SLUG` is the organization slug
- `$IX_SLUG` is the IXP slug (optional, if not provided all IXPs will be synced)

## Data pushed to netbox

IxCtl Source of Truth:

- mac addresses
- MTU
- Prefixes (will also remove prefixes that are no longer in ixctl)