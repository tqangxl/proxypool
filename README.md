# A python async proxy crawler and proxy pool
[![Build Status](https://travis-ci.org/arrti/proxypool.svg?branch=master)](https://travis-ci.org/arrti/proxypool)

使用python asyncio实现的异步代理爬虫和代理池，根据规则爬取代理网站上的免费代理，在验证其有效后存入redis中，
定期扩展代理的数量并检验池中代理的有效性，及时移除失效的代理。
同时用aiohttp实现了一个server，通过访问相应的url来从代理池中获取代理。

## 环境
* Python 3.5+
* Redis
* PhantomJS(optional)
* Supervisord(optional)

## 依赖
* redis
* aiohttp
* bs4
* lxml
* pyyaml
* requests
* selenium

## 使用
### 参数配置
配置文件为`proxypool/config.py`，主要的配置项如下：
* `redis_host`, `redis_port`
  > redis的`host`和`port`，默认为`127.0.0.1`和`6379`。
* `upper_limit`, `lower_limit`, `upper_limit_ratio`
  > 代理池容量的上限和下限，当代理数量达到`upper_limit*upper_limit_ratio`时停止爬取代理网站，已爬取到的代理会继续验证入池。
* `check_cycle_time`, `check_interval_time`
  > 前者是检查代理池容量的周期时间，低于下限即开始爬取代理；后者是本次爬取结束后、下次检查之前的间隔时间。
* `validate_cycle_time`
  > 验证池中代理有效性的周期时间。
* `validate_ratio`, `validate_upper_limit`
  > 每次验证池中代理的比例以及上限。
* `validate_timeout`
  > 通过使用代理请求某个网站来验证代理的有效性，这是请求的超时时间。
* `delay`
  > 爬取代理网站各个网页之间的延迟时间。
* `phantomjs_path`
  > PhantomJS可执行文件的路径，用于一些复杂的代理网站的爬取。
* `host`, `port`, `server_on`
  > server的`host`和`port`，以及是否开启server的标志。
* `verbose`
  > 是否输出日志内容到stdout，默认为`False`。

### 日志配置
配置文件为`proxypool/logging.yaml`，提供了3种`logger`，默认级别都是`DEBUG`：
* `console_logger`：同时输出到stdout和`file_logger`的日志文件中，用于调试；
* `file_logger`：默认输出到`/tmp/proxy_pool.log`文件；
* `server_logger`：server的`logger`，额外记录了远程请求的地址，默认输出到`/tmp/proxy_pool_server.log`文件。

### 爬虫规则
位于`proxypool/rules`目录下。通过元类`rule_base.CrawlerRuleMeta`和基类`rule_base.CrawlerRuleBase`来管理爬虫的规则类，规则类的定义如下：
* `start_url`(必需)
  > 爬虫的起始页面。
* `ip_xpath`(必需)
  > 爬取IP的xpath规则。
* `port_xpath`(必需)
  > 爬取端口号的xpath规则。
* `page_count`
  > 爬取的页面数量。
* `urls_format`
  > 页面地址的格式字符串，通过`urls_format.format(start_url, n)`来生成第`n`页的地址，这是比较常见的页面地址格式。
* `next_page_xpath`，`next_page_host`
  > 由xpath规则来获取下一页的`url`（常见的是相对路径），结合`host`得到下一页的地址：`next_page_host + url`。
* `use_phantomjs`, `phantomjs_load_flag`
  > `use_phantomjs`用于标识爬取该网站是否需要使用PhantomJS，若使用，需定义`phantomjs_load_flag`（网页上的某个元素，`str`类型）作为PhantomJS页面加载完毕的标志。
* `filters`
  > 过滤字段集合，可迭代类型。用于过滤代理。
* `filters_xpath`
  > 爬取各个过滤字段的xpath规则，与过滤字段按顺序一一对应。

#### 已有规则
* [西刺代理](http://www.xicidaili.com/nn/)
* [快代理](http://www.kuaidaili.com/free/inha/)
* [360代理](http://www.proxy360.cn/default.aspx/)
* [66代理](http://www.66ip.cn/areaindex_1/1.html)
* [秘密代理](http://www.mimiip.com/gngao/)

#### 如何新增规则
通过继承`rule_base.CrawlerRuleBase`来定义新的规则类`YourRuleClass`，放在`proxypool/rules`目录下，
并在该目录下的`__init__.py`中添加`from . import YourRuleClass`，重启正在运行的proxy pool即可应用新的规则。

### 运行
* `python run_proxypool.py`
  > 定期检查代理池容量，若低于下限则启动代理爬虫并对代理检验，通过检验的爬虫放入代理池，达到规定的数量则停止爬虫。
* `python run_proxyvalidator.py`
  > 用于定期检验代理池中的代理，移除失效代理。
* `python run_proxyserver.py`
  > 启动server。
* `python run.py`
  > 在3个进程中分别启用上述3种功能。

### server
启动server后，访问`http://host:port/`（`host`、`port`定义在`proxypool/config.py`中）来检测是否成功运行，成功后，通过
* 访问`http://host:port/get`来从代理池获取1个代理，如：`'127.0.0.1:1080'`；
* 访问`http://host:port/get/n`来从代理池获取n个代理，如：`"['127.0.0.1:1080', '127.0.0.1:443', '127.0.0.1:80']"`；
* 访问`http://host:port/count`来获取代理池的容量，如：`'42'`。

### supervisord
Linux下可以使用supervisord来管理python进程，首先修改`supervisord/supervisord.conf`文件中的3个`command`中的路径，
然后执行`supervisord -c supervisord/supervisord.conf`启动supervisord，
访问`http://127.0.0.1:9001`即可通过网页来管理`run_proxypool.py`、`run_proxyvalidator.py`和`run_proxyserver.py`这3个进程。
其他使用方法可以参考[官方文档](http://supervisord.org/)。

## 测试
执行`pytest tests`运行测试，可选参数：
* `--runslow`运行耗时较长的测试；
* `--runptjs`运行需要Phantomjs的测试。
