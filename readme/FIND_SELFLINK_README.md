## What is a selfLink?
A selfLink is a server-defined URL of the resource.
A legal format be `https://www.googleapis.com/compute/v1/projects/project/zones/zone/instances/instance` or `projects/project/zones/zone/instances/instance`
## Example 1: Find the selfLink of a VM instance
### Use gcloud command:
    gcloud compute instances describe some-instance-name
After executing this command line, you can find a 'selfLink' field, which is the instance's selfLink.
### Use Google Cloud Console:
1. Go to **VM instance details** page
2. Scroll down and find a line showing: *Equivalent REST*
3. Click the blue *REST* link
4. A configuration file will pop up, and you can search for selfLink field through Ctrl + F