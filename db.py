"""数据库操作"""
#~~~~~~~~~~~~~
import pymysql

import os
from dotenv import load_dotenv      #用于读取.env文件中MySQL数据库里面的账号、密码等

load_dotenv()       #读取 .env 文件里的配置

###1、定义连接函数，Python连接Mysql里面的数据库（连接数据库）~~~~~~~~~~~~~~~~~~~~~~~
def get_connection():
    connection = pymysql.connect(
        host = os.getenv("db_host"),              #读取.env文件中的db_host，赋值给host(字符串)
        port = int(os.getenv("db_port")),         #port需要int类型，所以int()转化一下。把字符串 "3306" 转成整数 3306
        user = os.getenv("db_user"),              #读取.env文件中的db_user
        password = os.getenv("db_password"),      #读取.env文件中的db_password
        database = os.getenv("db_database"),      #读取.env文件中的db_database
        cursorclass = pymysql.cursors.DictCursor  #查询数据库的时候，不要把每一行数据返回成 tuple，改成 dict
    )
    return connection
"""
get_connection：  你把菜谱拿在手里，但没做菜
get_connection()：你照着菜谱做了，得到一盘菜（return 的东西）
菜谱 ≠ 菜。函数 ≠ 函数执行的结果。后文要执行该函数，必须有返回
"""

###2、定义查询函数
# 2.1 查询所有数据，并进行分页
def get_todos(page,page_size):
    connection = None   #提前初始化变量，防止 get_connection() 抛异常时 finally 里 connection 未定义
    try:
        connection = get_connection()       #获取数据库连接；如果连接失败，会抛出异常
        with connection.cursor() as cursor:
            cursor.execute("select * from todos order by id limit %s offset %s;",    #设置分页查询
                           (page_size,(page-1)*page_size) )
            result = cursor.fetchall()
    finally:
        if connection is not None:
            connection.close()

    return result      #return要放在最后，因为return 一执行，函数就立刻结束
"""
connection是和数据库建立的连接；cursor是通过这个连接执行SQL、获取查询结果的操作工具。
即先连接数据库 → 再从这个连接拿一个cursor来操作数据库；真正干活的是 cursor
而 connection 更像是数据库通信通道，它负责connection.commit()、connection.close()
一句话总结：connection 管“连接和事务”，cursor 管“SQL 和结果”。
"""
"""
最初未加工的代码如下：
    def get_todos():
        connection = get_connection()
        cursor = connection.cursor()
    
        cursor.execute("select * from todos;")
        result1 = cursor.fetchall()
    
        cursor.close()
        connection.close()
        return result1
"""

## 2.2 条件查询
# 2.2.1 根据id查询相关数据（只会查询到一条数据，所以不用分页）
def get_todo_id(id):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("select * from todos where id = %s;",(id,))
            result = cursor.fetchone()
    finally:
        if connection is not None:
            connection.close()
    return result


# 2.2.2 根据status查询相关数据
def get_todo_status(status,page,page_size):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("select * from todos where status = %s order by id limit %s offset %s;",
                   (status, page_size, (page - 1) * page_size))
            result = cursor.fetchall()
    finally:
        if connection is not None:
            connection.close()
    return result

# 2.2.3 根据title查询数据函数（用于做AI识别用户意图来修改数据）（如用户只会说修把“给李四发合同”的时间，deadline修改成***）
def get_todo_title(title,page,page_size):  #根据title模糊查询数据
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "select * from todos where title like %s order by id limit %s offset %s;",
                (f"%{title}%", page_size, (page - 1) * page_size)   )
            #前后的%,是SQL的"通配符"，表示"任意字符"
            #因为AI提取出来的title可能和数据库不完全一致，如数据库title为“买返程的车票”，AI提取出来的title是“买返程车票”
            result = cursor.fetchall()
        return result
    except Exception as e:
        print("get todo title error:", e)
        raise
    finally:
        if connection is not None:
            connection.close()

# 2.2.4 根据deadline查询函数
def get_todo_deadline(start_time, end_time, page, page_size):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """       
            select *
            from todos
            where deadline between %s and %s
            order by deadline
            limit %s offset %s
            """
            # SQL语句太长，单独出来成段
            offset = (page - 1) * page_size

            cursor.execute(sql,(start_time,end_time,page_size,offset))  #引用上面的SQL语句
            return cursor.fetchall()
    finally:
        connection.close()

#~~~~~~~~~~~~
### 3、查询获取所有title的函数 （用于返回数据库所有任务）
def get_all_titles():
    connection = None
    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "select id,title from todos;"
            )
            result = cursor.fetchall()

    finally:
        if connection is not None:
            connection.close()

    return result


### 4、定义增加函数
def add_todo(title,deadline):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("insert into todos (title,deadline) values (%s,%s);",
                   (title,deadline))

            new_id = cursor.lastrowid   #刚刚 insert 进去那条数据的 id。
                #lastrowid 返回一个整数，是上一条 INSERT 语句生成的 AUTO_INCREMENT 主键值

        connection.commit()     #提交
    except Exception:
        if connection is not None:
            connection.rollback()
        raise       #把当前异常继续往上抛
    finally:
        if connection is not None:
            connection.close()
    return new_id   #返回新加的数据的ID


### 5、修改函数
#根据id修改全部（即status和deadline）
def update_all(id,status,deadline):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("update todos set status = %s,deadline = %s where id = %s;",
                   (status,deadline,id))
            affected_row = cursor.rowcount   #就是把“这次 update 影响了几行”这个结果保存下来，等 cursor 关闭以后还能继续使用
            # rowcount返回一个整数，表示刚才执行的SQL影响（修改 / 删除 / 插入）了多少行
        connection.commit()
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()
    return affected_row     #返回修改了几条数据



### 6、删除函数
def delete_todo(id):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("delete from todos where id = %s;",
                   (id,))
            deleted_row = cursor.rowcount    #把"刚才 SQL 影响了几行"这个数字，存到 result 里
        connection.commit()
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()
    return deleted_row      #返回删除了几条数据

### 7、定义查询数据总条数函数
def get_todo_count():
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:

            cursor.execute("select count(*) as count from todos")   #给查询到的数量结果取名count
            result = cursor.fetchone()
    finally:
        if connection is not None:
            connection.close()

    return result["count"]     #return要放在最后，因为return 一执行，函数就立刻结束

### 8、定义查询某状态的数据总条数的函数
def get_todo_status_count(status):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "select count(*) as count from todos where status = %s;",
                (status,)
            )
            result = cursor.fetchone()
            #count(*) 是聚合函数，它会把符合条件的多条数据统计成一个数字。用 fetchone()
    finally:
        if connection is not None:
            connection.close()

    return result["count"]

### 9、定义查询某title关键字的数据总条数的函数
def get_todo_title_count(title):
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "select count(*) as count from todos where title like %s;",
                (f"%{title}%",)
                #标题中包含这个关键词的Todo一共有多少条
            )
            result = cursor.fetchone()
    finally:
        if connection is not None:
            connection.close()
    return result["count"]

### 10、定义查询某deadline范围内数据的总条数
def get_todo_deadline_count(start_time, end_time):

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            sql = """
            select count(*) as total
            from todos
            where deadline between %s and %s
            """
            #SQL语句太长了，独立出来单独成段

            cursor.execute(sql,(start_time,end_time))
            return cursor.fetchone()["total"]

    finally:
        connection.close()

### 11、根据多个可选条件查询具体的 Todo 数据
def get_todo_advanced(
        title=None,
        status=None,
        start_time=None,
        end_time=None,      #表示这些参数，如果不上传就默认未None
        page=1,
        page_size=10):
    """
    支持：
        title 模糊查询
        status 查询
        deadline 开始时间
        deadline 结束时间
        分页
    """
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            sql = """
            select *
            from todos
            where 1=1       
            """
            #where 1=1是一个永远成立的条件，就是一个占位条件。   #作用：方便后面不断追加 and条件
            #sql语句单独成段，后续可直接引用

            params = []     #定义一个空列表，用于保存 SQL中 %s 对应的参数


            if title:      #判断 title 有没有值。只有get_todo_advanced()上传了title参数，才会执行下面代码
        #get_todo_advanced(title="牛肉")，上传了title参数，即title="牛肉"，此时if title为True,执行下面代码

                sql += " and title like %s"     #给原来的 SQL 后面继续增加条件（title模糊查询）
        #起初sql语句为：select * from todos where 1=1，执行本行代码后，相当于sql = sql + " and title like %s"
        #SQL语句变成了select * from todos where 1=1 and title like %s
                params.append(f"%{title}%")

            if status:
                sql += " and status = %s"       #status 精确查询
                params.append(status)


            if start_time:                      #deadline 时间范围查询
                sql += " and deadline >= %s"
                params.append(start_time)


            if end_time:
                sql += " and deadline <= %s"
                params.append(end_time)


            sql += " order by id limit %s offset %s"        #分页
            #上面4个条件给SQL语句添加 where后，本行代码给动态 SQL 加上排序和分页，然后执行 SQL，获取查询结果。

            params.append(page_size)
            params.append((page - 1) * page_size)

            cursor.execute(sql, params)
            result = cursor.fetchall()

    finally:
        if connection is not None:
            connection.close()

    return result

### 12、查询符合上面这些根据多个可选条件查询具体的 Todo 数据，一共有多少条。
def get_todo_advanced_count(
        title=None,
        status=None,
        start_time=None,
        end_time=None):

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:

            sql = """
            select count(*) as count
            from todos
            where 1=1
            """
            params = []

            if title:
                sql += " and title like %s"
                params.append(f"%{title}%")

            if status:
                sql += " and status = %s"
                params.append(status)

            if start_time:
                sql += " and deadline >= %s"
                params.append(start_time)

            if end_time:
                sql += " and deadline <= %s"
                params.append(end_time)

            cursor.execute(sql, params)

            result = cursor.fetchone()

    finally:
        if connection is not None:
            connection.close()

    return result["count"]
