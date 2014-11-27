##Spider
---

####环境设置

依赖环境：

	python v2.7 or higher than
	redis  # a key/value pairs database.
	mongodb # a document-oriented database.
	
python 依赖模块：

	chardet
	PyYaml
	gflags
	pymongo
	redis
	pycurl
	
其它类库

	lxml
	ibxml2-dev 
	libxslt1-dev

爬虫抓取数据分两步


####第一步，抓取url列表，也就是每个要被采集的页面链接，抓取url列表需要使用url_collection.py

url_collection.py

使用方法

	./url_collection.py --configure=./rules/kickass.yaml
	
	
####第二步，抓取具体页面，当完成第一步后，url被写入redis，此时需要第二步采集具体页面。

	./spiders/kickass.py --configure=../rules/kickass.yaml
	
	
	
mongodb 数据结构

	每个爬取站点使用一个库，默认惯例使用域名作为库名，例如：example.com 则使用 example 作为库名。
	
	每个库下分为集合：
	
		urls          # 抓取链接, urls 这个为了效率可以存放在redis中。
		data          # 抓取的数据
		attachments   # 网站的相关附件
		
####全局配置

	全局配置文件存储在 config/config.yaml
	
	# 项目说明

	proxies 设置所有代理条目
	
		  - name: none
		    type: http
		    host: 192.168.1.1
		    port: 8080
		  - name: none1
		    type: https
		    host: 192.168.1.2
		    port: 8080
		
		
		
####抓取配置

	settings: # 全局配置
	    spider: kickass # 爬虫名称
	    base_url: http://kickass.to  # 基础url
	    cookie: 'lang_detected=en; lang_code=en; captcha_hash=9410c0fbf30dc4963cb9451e2edab0b3; _spc=d17366a7-70ad-c92c-8d16-c76df2a35c5d; _ga=GA1.2.1569526442.1392654840; country_code=CN; state=1395237703988' # 抓取时需要的cookie，可为空。
	    enable_proxy:True|False|specify proxy name # 开启代理采集, 指定非boolean则使用指定代理采集

	storage:      # 存储配置
      - name: mongodb
        driver: mongodb
        db: kickass
        host: 127.0.0.1
        port: 27017
        
      - name: redis
        driver: redis
        host: 127.0.0.1
        port: 6379
        db: 15
        
        
        
	collection: # 需要抓取的url集合
	    - name: movies
	      # 集合名称
	      
	      url: http://kickass.to/movies/{page}/ 
	      # 待抓取的url模板， 其中{page是占位符}
	      
	      range: 1-400 
	      # 分页范围，相当于替换{page}占位符
	      
	      rules: {rule: '<a href="(.*?)" class="cellMainLink">(.*?)</a>', attributes: {url: 0, title: 1}} 
	      # 抓取规则，抓取规则是一个多项配置，其中包括： 
	      	rule 抓取规则
	      	attributes 抓取的属性，可包含多项，对应抓取规则中的规则符号，需要注意的是这里的展位规则从0开始。
	      
	      proxy: https://www.proxy.com
	      
	      # 设置代理，可应用到每个独立的collection。
		......

	
	attributes:  # 抓取内容页面的属性
	    - name: title 
	      # 属性名称
	      
	      rule: <title>(.*?)Torrent - KickassTorrents</title>
	      # 抓取规则
	      
	      position: 1
	      # 抓取规则定位, 需要注意的是，这里的规则占位符需要从1开始，0是取全部的匹配文本。
	      
	      middleware: downloader
	      # 调用中间件，例如如果某个属性中包含附件需要下载可以调用下载中间件。
	      
	      # *trim 分别用于处理字符前后，字符前，字符后的空白字符
	      trim: true | false
	      ltrim
	      rtrim
	      
	      
	      # callback 用于自定义处理某个属性。
	      callback: method_name
	

		  # 用于处理多个属性的集合，例如采集内容页中的tags，tags可能是多个（一个集合）
	      multiple: true
	      
	      
	      # 设置采集块区域的起始位置和结束位置	      
	      content_range: <div class="content">(.*?)</div>
	      
	      # content_range_position 用于定位内容的属性
	      content_range_position: 设置采集块区域的结束位置

	      
	      
	      