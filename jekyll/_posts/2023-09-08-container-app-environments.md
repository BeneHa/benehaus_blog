---
title: "Upgrading to container app environment workload profiles - or not?"
image: assets/images/blogposts/2023-09-08-cappenv/logo.jpeg
categories: [ Azure ]
---

## What are container apps?

Azure container apps are an Azure service that has been around since [May 2022](https://azure.microsoft.com/en-us/updates/generally-available-azure-container-apps/). It is a container as a service solution, meaning you just deploy a container there and do not need to worry about the underlying Kubernetes that Azure will manage for you. Initially, the service was completely serverless and you were billed by vCPU core seconds that you consume.

Later they announced workload profiles which went GA [end of August](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/generally-available-azure-container-apps-workload-profiles-more/ba-p/3913345). These enable you to run on larger machines and use a dedicated capacity of vCPU and vRAM for your containers.

## Two different environments

Now that workload profiles existed, there were two types of environments you could deploy:
- Consumption only: Essentially the old kind of container app environment
- Consumption + Dedicated: Enables you to use workload profiles, but also run apps in a consumption-based environment like in the old plan

Additionally the consumption + dedicated plan supports UDRs, an important feature for companies running applications in a hub and spoke architecture. This feature was supported in the original container apps but then later moved to be only supported in workload profile environments. The information that consumption only environments do not support UDRs any more was added to the documentation [here](https://github.com/MicrosoftDocs/azure-docs/commit/08ff85c5075de83efa5827bc43a489906786973a#diff-fb59801b9fa019798f46419f4d51fd761cc2d72aa98a4d7d8dfb03d7a6dd7367R25).

## The problem

While UDRs are stil working with the old profile type, they are not officially supported any more and so using them can lead to weird effects for which the Microsoft support will not help you as you are using an unsupported feature. I observed this when doing a tag change on the environment crashed the entire environment, a behaviour which should never happen considering tags are just convenience features for the resources.

## How to upgrade

So, what is the advantage of the consumption only plan? Well, as far as I can tell, there is none. It feels like an old version of a service that Microsoft is keeping around for compatibility reasons. Which would be fine, if there was a way to upgrade existing environments to the consumption + dedicated plan. But there is none. If you provisioned your environments a year ago, you are stuck with the old version and need to set up a new environment with new networking, firewall rules etc., especially if you are using UDRs which used to be supported there. This can mean a huge effort for migrating to a new version of a service which is 1.5 years old.

## Workarounds

There is a workaround to keep using the old environment while using UDRs which is described in this [Github issue](https://github.com/microsoft/azure-container-apps/issues/227#issuecomment-1350257333). But who knows if this workaround will keep working permanently?

## Conclusion

The cloud landscape and its services change fast these days and that is all right. However, when you introduce a new service, customers should not have to do a complicated migration after 1.5 years because they are in an old version of the service already. Please, Microsoft - if you make these kinds of changes to your service, provide an upgrade path that is easiert than just building everything again from the ground up.
