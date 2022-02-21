<div id="top"></div>


<h3 align="center">ECE1779 Project 1</h3>

  <p align="center">
    Web Development
    <br />
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

[![Product Name Screen Shot][product-screenshot]](https://example.com)

This project is a web application for booru-like image upload and browse, created for group assignment of *course ECE1779* at **[University of Toronto](utoronto.ca)**

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Getting Started

### Prerequisites

The project uses python. Main packages for this project are:

* python>=3.8
* flask>=2.0.2
* mysql-connector
* requests

We recommend using anaconda to install the prerequisites using the code as follows:

`conda create -f environments.yml`

You can also install via pip3 by first activating your venv and use:

`pip3 install -r requirements.txt `



### Installation

#### **How to start and login to the instance**

1. After login to IAM user, turn to [EC2 console](https://console.aws.amazon.com/ec2/v2/home), select “**instances**”, select instance ID `i-04bd5d1898f6dbbfc` and boot. (There should be only one instance among all)We recommend using ssh to login to the EC2 instance but you can also login by simply selecting “**EC2 Instance** **Connect**” with entering username “**ubuntu**”. Code for logging in is as follows:

   ```
   ssh -i "path/to/your/public-key.pem" ubuntu@ec2-44-203-50-20.compute-1.amazonaws.com
   ```

#### How to run the code

1. `git clone https://github.com/ephemer1s/ece1779h-a1.git`
2. Run `bash start.sh` and the web application will start running. The shell script should be in the home directory.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

Open port 5000 or the port you run flask on before initializing the server.

#### How to obtain the public IP address?

* `dig +short myip.opendns.com @resolver1.opendns.com`

<p align="right">(<a href="#top">back to top</a>)</p>

#### **How to use our website**

You should find 5 buttons on the main page. 

* To upload a key/image pair, click “**Upload**”.
* To get an image corresponding to a key, click “**Browse**”.
* To obtain all keys currently in the database, click “**Key** **List**”.
  * Note: What shows in the KeyList page may not 100% accurately reflect the existence of images in the filesystem. This is because we wanted to preserve the key/image pair even when the web app shuts down, which may cause the local filesystem to no longer be in sync with the database (e.g. If someone plays with the filesystem). Theoretically this should not happen in normal use cases.
* To configure memcache capacity and policy, click “**Config**”.
* To see the statistics of the memcache within the last 10 minutes, click “**Statistics**”
* After completing a certain task, please visit the main page manually for now.

<!-- General Architecture -->

## General Architecture

* The app takes two flask instances (Frontend, which displays the website and deals with user requests; and Backend, which is memcache) on a multi-threaded runner.
* Using a MySQL database, the frontend saves and loads key/image_path pairs from the database and uses the backend memcache for faster access if possible, to (theoretically) lower the time it takes to complete the request due to not needing a response from the database. 
* Images are passed between APIs using base64 format and decoded on runtime.

<!-- CONTACT -->

## Contact

Jianyu Wen - sam.wen@mail.utoronto.ca

Haozhe Wang - haozhe.wang@mail.utoronto.ca

Haocheng Wei - haocheng.wei@mail.utoronto.ca

Project Link: [https://github.com/ephemer1s/ece1779h-a1](https://github.com/ephemer1s/ece1779h-a1)

<p align="right">(<a href="#top">back to top</a>)</p>

## **Database Schema** 

Our MySQL database hosts 3 tables that store data for frontEnd and backEnd to use. Database relations are presented as follows: ![img](https://lh4.googleusercontent.com/q44tvqIHN2iBLfU0TTWdJLKWCmydQDyEbSyvh9JSjPwik3_Bzqb4ex7tEZDo5Vtg0P3m6tVgTffTIKOZPyThXI6tTyieOJMY4aa2bGGL8f860XosD3E8egJXLO2W9ZAq-OH_Kh3q)  

* **Keylist (keyID, path)**

  Keylist table stores all the keys with their corresponding local file system storage path in EC2. *keyID* is the primary key in this table, storing the key uploaded by the user. *path* keeps the relative path of the image stored in the local file system in text type. Web functions could select *keyID* and acquire the relative path of the target file.

* **Configuration (id, capacityB, replacePolicy)**

  Configuration table saves the current configuration parameters that the memcache applies. *id* is the primary key used to specify the row to update. *capacityB* tells the memcache storage capacity in B. It is worth mentioning that any function has to convert its capacity value in MB into value in byte by multiplying by 1048576 before updating it into the database. *replacePolicy* keeps the cache replacement policy applied right now. We use 0 to represent Random Replacement policy and 1 to represent Least Recently Used policy.

* **Statistics (id, itemNum, itemTotalSize, requestNum, missRate, hitRate)**

  Statistics table reflects the real-time operation status parameters of the memcache. Same as below, *id* is the primary key used to specify the row to update. *itemNum*, *itemTotalSize,* and *requestNum* indicate the number of items, the total file size of all items in byte in the memcache right now, and the number of memcache get request served. *missRate and hitRate* refer to the memcache miss and hit rate of get request of the past 10 minute. Statistics table will be updated by memcache backEnd every 5 seconds.

It is worth noting that the Keylist table could have multiple rows to store paths for numbers of keys, but Configuration and Statistics tables are supposed to have only one single row to store current configuration setting or statistics data. Therefore, we set up 2 triggers in our MySQL database to prevent unexpected inserts to the Configuration and Statistics tables. Once there is already one row in the table, any other insert query would not be allowed.

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#top">back to top</a>)</p>

