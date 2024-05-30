# Personal blog of Benedikt Häuser

My personal blog where I infrequently write whatever comes to my mind.
Visit [here](https://www.bene.haus).

**Starting container:**
docker build . -t jekyll
cd jekyll
docker run -p 4000:4000 -v $(pwd):/site  jekyll
