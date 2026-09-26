### SQL 文件主要负责初始化数据库结构
# 1、建库
create database if not exists AI_todo;
# 2、切库
use AI_todo;
# 3、建表
create table if not exists todos(
    id int primary key auto_increment,
    title varchar(50) not null,
    deadline datetime,
    status varchar(15) default 'pending',
    created_at datetime default current_timestamp
);
#1、2、3建表、切库、建表。SQL 文件主要负责初始化数据库结构
#~~~~~~~~~~~~~~~~~下面的内容都可以去掉（只是为了验证）~~~~~~~~~~~~



# 4、插入表数据
insert into todos (title, deadline)     #因为有3个列不用手动上传，所以必须要上传列明
    values ('给张三发合同','2026-10-01 15:00:00');     #日期必须是字符串形式包裹
# 5、查询数据
select status from todos where status='pending';
# 6、修改数据
update todos set title = '给张三发合同并确认签署' where title = '给张三发合同';
# 7、再新加一行数据
insert into todos (title, deadline)     #因为有3个列不用手动上传，所以必须要上传列明
    values ('给李四发合同','2026-9-28 15:00:00');
# 8、删除数据
delete from todos where id in (13,14,15,16);

select * from todos;

delete from todos where id in (50);