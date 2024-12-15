#!/bin/bash

#reading the value of weekday.txt file into the var variable
rpass=$(cat .mysql_root_password)
mpass=$(cat .mysql_merterre_password)

add_merterre_raw=$(cat create_merterre.sql)
add_merterre="${add_merterre_raw/BY /BY \'"$mpass"\'}"

mysql -h localhost --user=root --password=$rpass -se "$add_merterre"
