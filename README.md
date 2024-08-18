# Personal blog of Benedikt Häuser

My personal blog where I infrequently write whatever comes to my mind.
Visit [here](https://www.bene.haus).

## Structure
- .github: workflows to deploy the website and the Azure Functions
- getData: function to download new data from Komoot
- jekyll: the static website components
- processData: process the komoot data in the storage account to create diagrams
- synchronizeToStrava: upload new gps tracks to Strava automatically
- terraform: IaC setup for all necessary infrastructure

**Starting container:**
docker build . -t jekyll
cd jekyll
docker run -p 4000:4000 -v $(pwd):/site  jekyll
