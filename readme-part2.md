# readme for part2
 
* [1] สำหรับสร้าง brach ชื่อ part2
* [2] detting database to posrgresql
   * install posrgresql
      scoop postgresql
   * stat posrgresql
      pg_ctl start
   * create database and user/passeord
      psql -U postgres
      create usre transformer eith passwoed='1234';
      create database transformerdb whit owner=transformer;
   * write models.py
   * makemigrations
   * migrete