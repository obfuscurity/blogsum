
# Blogsum
# Copyright (c) 2009 Jason Dixon <jason@dixongroup.net>
# All rights reserved.


###########################
# pragmas                 #
###########################
package Blogsum::Config;
use strict;


###########################
# user options            #
###########################
our $database = 'data/site.db';
our $tmplfile_index = 'templates/index.html';
our $tmplfile_admin = 'templates/admin.html';
our $blog_title = 'example.com';
our $blog_subtitle = 'My New Blog';
our $blog_url = 'http://www.example.com/';
our $blog_owner = 'user@example.com';
our $blog_rights = 'Copyright 2009, Example User';
our $feed_updates = 'hourly';
our $captcha_pubkey = '';
our $captcha_seckey = '';
our $comment_max_length = '1000';
our $comments_allowed = 0;
our $smtp_server = 'localhost:25';
our $smtp_sender = 'blogsum@example.com';
our $timezone_offset = '+0';
our $articles_per_page = '10';
our $google_analytics_id = '';
our $google_webmaster_id = '';

1;

