---
title: "Handling Snowflake allowlists with terraform"
image: assets/images/blogposts/2025-07-30-snowflake-firewall/firewall.jpg
categories: [ Azure, Snowflake ]
---

In this blog post I will show you how to handle Snowflake network rules and policies via terraform, with a focus on Azure IPs which can get changed all the time.

## The problem

In my company we need to have Snowflake access limited to the minimal set of IP ranges possible, but we have different sources from where requests can come to Snowflake.
These include:
- ZScaler (our VPN service)
- on-premise egress with fixed IPs
- different Azure services which get new IP ranges regularily
- dbt Cloud

So I set up an automation with terraform to handle all this automatically.

## Snowflake network rules

Snowflake now collects IP ranges to allow or forbid in network rules, which are then attached to network policies.

### dbt

A policy is assigned to your whole Snowflake account or individual users or integrations. In terraform this looks like this:

```terraform
resource "snowflake_network_rule" "dbt" {
  name       = "DBT"
  database   = "UTIL_DB"
  schema     = "PUBLIC"
  comment    = "DBT IP address"
  type       = "IPV4"
  mode       = "INGRESS"
  value_list = ["3.123.45.39", "3.126.140.248", "3.72.153.148"]
}
```
DBT cloud publishes its IPs [here](https://docs.getdbt.com/docs/cloud/about-cloud/access-regions-ip-addresses) and they never change, so this is the easy case.

### ZScaler

It gets a bit more complicated with ZScaler, because you always have to get their latest set of IPs [here](https://config.zscaler.com/api/zscaler.net/hubs/cidr/json/recommended). We download them with the terraform http provider:

```
data "http" "zscaler_ips" {
  url = "https://config.zscaler.com/api/zscaler.net/hubs/cidr/json/recommended"

  lifecycle {
    postcondition {
      condition     = (200 == self.status_code)
      error_message = "Status code invalid"
    }
  }
}
```
and then process them in a locals expression:
```
  zscaler_ipv4_ranges = [for r in jsondecode(data.http.zscaler_ips.response_body).hubPrefixes : r if !strcontains(r, ":")]
```
This filters out IPv6 values which we do not want. You can now use the resulting set of IPs in a network rules resource like shown above.

### Azure

The most complicated case is Azure. You can download their latest IP range file on [this page](https://www.microsoft.com/en-us/download/details.aspx?id=56519). But there is no fixed link for a latest version, so we have to figure out the link first:
```
data "http" "azure_ip_download_page" {
  url = "https://www.microsoft.com/en-us/download/details.aspx?id=56519"
}
``` 
Then we parse the downloaded page using regex to find the link to the latest document:
```
locals {
    azure_ip_download_link = regex("https://download\\.microsoft\\.com/download/[a-zA-Z0-9_\\/-]*ServiceTags_Public_[0-9]*.json", data.http.azure_ip_download_page.response_body)
}
```
And then we can download the actual list of IP ranges:
```
data "http" "azure_ip_ranges" {
  url = local.azure_ip_download_link
  lifecycle {
    postcondition {
      condition     = (200 == self.status_code)
      error_message = "Status code invalid"
    }
  }
}
```
Now you just have to filter out the relevant part of the list, e.g. for PowerBI, and get rid of IPv6 addresses:
```
locals {
  azure_ip_ranges_powerbi_object = [for d in local.azure_ip_ranges_full : d if d["name"] == "PowerBI"][0]
  azure_ip_ranges_powerbi        = [for r in local.azure_ip_ranges_powerbi_object.properties.addressPrefixes : r if !strcontains(r, ":")]
}
```

And there you go, you now have the current up to date version of the IP ranges that you can apply in a Snowflake network rule.
Every time your run terraform apply, the latest version of the file will get downloaded. So you can set up a simple automation to run this every morning and update the IP ranges automatically, and you will never have to worry about this again.
