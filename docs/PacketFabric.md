
# PacketFabric Integration

### Workflow

1. Customer signs up at UIX, selects PF location, enters $customer_uniq_id
2. UIX to customer: vc_member_crid / market code - email link to click on to bring up the PF portal and create the VC
3. Customer requests VC, which $notifies UIX
  - Goes to portal, clicks Virtual Circuits, click the +, then click 3rd Party
  - or click https://portal.packetfabric.com/virtual-circuits/create/2
4. UIX provisions user, port to quarantine, posts to PF `/virtual-circuits/requests/:vc_request_id/provision`
5. UIX runs get mac-provision-prod, email user welcome packet


### Workflow v2 (WIP)

1. Customer signs up at UIX, selects PF location, enters $customer_uniq_id
2. UIX to customer: vc_member_crid / market code - email link to click on to bring up the PF portal and request the VC
3. Customer requests VC, which $notifies UIX
  - Goes to portal, clicks Virtual Circuits, click the +, then click 3rd Party
  - or click https://portal.packetfabric.com/virtual-circuits/create/2
4. UIX provisions user, port to quarantine, approves the VC request, emails welcome packet
5. Customer provisions port
6. UIX runs getmac, provision-prod


*NOTE* this would result in UIX paying currently.

1. Customer signs up at UIX, selects PF location, enters vc_member_crid
2. UIX provisions user
3. UIX post to PF `/virtual-circuits/third-party-connections/evpl`
4. Customer to PF, assign the
5. Customer to UIX,


### References

https://docs.packetfabric.com/#api-Virtual_Circuits-PostVirtualCircuitsRequests

https://portal.packetfabric.com/interfaces


