



## Jekyll

## Namecheap

## Azure Portal - Storage account

Next, let's head over to portal.azure.com and create some resources there. I am assuming you have a subscription with a payment method set up. First, we create a Resource Group by searching for "Resource Group" in the top search bar, clicking on it, then on "Create" and then we enter the desired name and location:

{% include image.html
    url="/assets/images/blogposts/2022-08-12-blog-setup/3_azure_create_rg.png"
    description="Creating a resource group in the Azure portal"
    alt="Azure resource group" %}

We will put all necessary resources into this resource group. Let's create the first one right away. Select the resource group, click on "Create resource" and search for "storage account". Click on the search result and create it. Here you have some more options. Select a name, location and locally redundant storage (this is enough for a non-critical use case like a website) and create it:

{% include image.html
    url="/assets/images/blogposts/2022-08-12-blog-setup/4_azure_create_storage.png"
    description="Creating the storage account"
    alt="Azure storage account" %}

On the Blob storage, click on "Static website" in the menu and set it to Enabled. Enter "index.html" and "404.html" for the required documents and click on save. You can now see your primary endpoint which will look something like https://blobname.z1.web.core.windows.net. Your website can now be reached at that URL if you put a index.html file into the container "$web" that was created automatically.

## Github - deploy website

Now we want our website to be deployed to this storage account. Got to Github, create a repository and push you code.