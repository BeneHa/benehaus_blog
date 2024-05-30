---
title: "Permission issues when restoring an Azure PostgreSQL server"
image: assets/images/blogposts/2023-06-03-postgres/logo.png
categories: [ Azure ]
---

## The problem

We recently ran into a permission issue related to creating and restoring an Azure PostgreSQL flexible server which I thought could also happen to other teams so I will share it here.

When using private networking with private endpoints etc., a Postgres server needs a private DNS zone to which it can create a VNet link. In many corporate setups, networking is managed with a central networking team, while different development teams want to create databases for their applications. When you create a Postgres database and you pass in the centrally managed postgres private DNS zone (privatelink.postgres.database.azure.com), this works as long as the user creating the database has the permission to join a private DNS zone. This fits well into the hub and spoke idea where the development teams should not need any editing rights on central infrastructure components.

The case is different if you want to restore a Postgres server. Basically, restoring is just like creating a new server but from an older backup. When it comes to Azure permissions however, the previously created VNet link is now a subresource of the postgres private DNS zone. For some reason the resore operation does not use this VNet link but wants to recreate it, so it needs write permissions on it. As explained before, this means that a development team needs write access to centrally managed resources which is probably not desired. That this permission is even necessary is also strange because restoring a server should not require more permissions than creating an entirely new one.

## The workaround

The workaround we are using for now is to give the development teams Contributor permissions on the VNet link from their VNet to the private DNS zone in the hub, so we keep the scope of permissions in the hub as limited as possible.

## The Microsoft answer

We discussed this issue with Microsoft support and they agreed there should be an option to skip the recreation of the VNet link for a database restore. They said they have put this on the development roadmap (this was beginning of June 2023). Let's see how long it takes :)

## Update
The vnet linking has now been made optional as described (here)[https://techcommunity.microsoft.com/t5/azure-database-for-postgresql/dns-zone-linking-is-no-longer-enforced-when-creating-azure/ba-p/3911877].
