



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

Now we want our website to be deployed to this storage account. Got to Github, create a repository and push you code. Now, head to the settings of your repository and go to Secrets -> Actions. Create new repository secrets:
- STORAGE_ACCOUNT_NAME is the name of the storage account you created
- SAS_TOKEN: In the Azure portal, got to you storage account and "Shared access signature". Create a token with write permissions to the Blob service and Container resource type that is valid for a year

Now create a  file defining the Github Action workflow in .github/workflows/main.yml:
```
name: Build and deploy Jekyll site to Azure Blob static page

on:
  push:
    branches:
      - 'main'

jobs:
  jekyll:
    runs-on: ubuntu-20.04
    steps:
    - uses: actions/checkout@v2
    - uses: actions/cache@v1
      with:
        path: vendor/bundle
        key: ${{ runner.os }}-gems-${{ hashFiles('**/jekyll/Gemfile.lock') }}
        restore-keys: |
          ${{ runner.os }}-gems-
    # Standard usage
    - uses: lemonarc/jekyll-action@1.0.0
    - uses: bacongobbler/azure-blob-storage-upload@v1.2.0
      with:
        source_dir: '_site'
        container_name: $web
        sas_token: ${{ secrets.sas_token }}
        account_name: ${{ secrets.storage_account_name }} 
        extra_args: --overwrite True
        sync: true
```

This will build the Jekyll page and deploy the folder with the built website code (_site) to the storage account container $web. Ideally, after pushing this file, Github should recognize it and run the deployment job automatically because we set it to trigger on the main branch.

{% include image.html
    url="/assets/images/blogposts/2022-08-12-blog-setup/5_github_action.png"
    description="Triggering a Github action"
    alt="Github action" %}

## CDN refresh