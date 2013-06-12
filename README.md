Blogsum
=======

The following instructions were ported from an older document hosted on an earlier Trac server. Blogsum was designed for running in OpenBSD's httpd chroot. Although there have been ports to other operating systems, this document is solely
intended for OpenBSD users.

## Installation

### The Easy Way

OpenBSD -current users can install Blogsum from -current ports/packages. Blogsum (and dependency p5-HTTP-Lite) were added after OpenBSD 4.6.

  $ sudo pkg_add -i blogsum

And then follow the instructions in `/var/www/blogsum/docs/README.OpenBSD` to complete the setup. 

### The Almost-As-Easy Way

#### Dependencies

Required:

```
$ sudo pkg_add -i mod_perl p5-DBI p5-DBD-SQLite p5-HTML-Template p5-XML-RSS p5-HTTP-Lite git
$ sudo /usr/local/sbin/mod_perl-enable
```

Optional (needed for WordPress migration script):

  $ sudo pkg_add -i p5-XML-Simple

#### Download

```
$ cd /var/www
$ sudo git co https://github.com/obfuscurity/blogsum.git
```

#### Create the Database

```
$ cd /var/www/blogsum
$ sudo sqlite3 data/site.db < examples/create_sqlite.sql
$ sudo chown -R www data
```

Optional (for importing WordPress xml):

  $ sudo examples/wp2blogsum.pl /path/to/export.xml data/site.db

### Configuring Blogsum

First, create your local configuration.

```
$ sudo cp /var/www/blogsum/Blogsum/Config.pm.dist /var/www/blogsum/Blogsum/Config.pm
$ sudo $EDITOR /var/www/blogsum/Blogsum/Config.pm
```

Remaining steps:

* If comments will be enabled, visit the CAPTCHA project and register your account. Add your keys to Config.pm.
* Edit `/var/www/blogsum/examples/httpd-blogsum.conf` for your site and place it somewhere appropriate (e.g. `/var/www/conf/modules/`).
* Create your `AuthUserFile` as defined in `httpd-blogsum.conf`.
* Edit your `httpd.conf` to `Include` your `httpd-blogsum.conf`.
* Enable `rewrite_module`, `proxy_module` and `perl_module` in `httpd.conf`.
* (Re)start your Apache.
