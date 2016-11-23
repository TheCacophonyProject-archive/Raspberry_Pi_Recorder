# Raspberry_Pi_Recorder
Combining the Thermal and IR recorder to be able to run on one Raspberry Pi

## License
This project is licensed under the GPL-V3

### Licence disclaimer
The Cacophony Project will, upon request, consider making code in this
repository available under the MIT license if doing so maximises our
impact for the benefit of NZ's native ecosystems. We will not do this
lightly.

We ask that open source contributors, who will hold copyright over
significant project contributions, alert us if they find this
possibility unacceptable. To minimise complexities in contribution, we
will endeavour to seek permission of contributors we can easily contact
before altering the license to MIT, however if we are unable to contact
contributors readily, we will assume consent.

## Setup
Install ffmpeg with H264
http://www.jeffreythompson.org/blog/2014/11/13/installing-ffmpeg-for-raspberry-pi/

Install pyepton  
`sudo apt-get install python-opencv python-numpy`  
`git clone https://github.com/groupgets/pylepton.git`  
`cd pylepton/`  
`sudo python setup.py install`  

Enable camera, SPI, I2C, and change Timezone on the Raspberry Pi.


Clone repo.  
`cd`  
`git clone https://github.com/TheCacophonyProject/Raspberry_Pi_Recorder.git`

Clone config file and set params.   
`cd Raspberry_Pi_Recorder`    
`cp config_TEMPLATE.txt config.txt`  
Set the server url to the url of the server you are uploading to.  
Set the group to the groupname of a group that you have created on the server.  
 
Run app with:  
`python main.py`

When running the app for the first time it should say that it registered the new device.

