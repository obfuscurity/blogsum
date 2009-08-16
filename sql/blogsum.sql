CREATE TABLE articles (id integer primary key, date date, title text, uri text, body text, tags text, enabled boolean, author text);
CREATE TABLE comments (id integer primary key, article_id integer, date date, name text, email text, url text, comment text, enabled boolean);
