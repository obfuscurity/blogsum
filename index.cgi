
# Blogsum
# Copyright (c) 2009 Jason Dixon <jason@dixongroup.net>
# All rights reserved.


###########################
# pragmas and vars        #
###########################
use strict;
use Blogsum::Config;
my $database = $Blogsum::Config::database;
my $tmplfile_index = $Blogsum::Config::tmplfile_index;
my $blog_title = $Blogsum::Config::blog_title;
my $blog_subtitle = $Blogsum::Config::blog_subtitle;
my $blog_url = $Blogsum::Config::blog_url;
my $blog_owner = $Blogsum::Config::blog_owner;
my $blog_rights = $Blogsum::Config::blog_rights;
my $feed_updates = $Blogsum::Config::feed_updates;
my $captcha_pubkey = $Blogsum::Config::captcha_pubkey;
my $captcha_seckey = $Blogsum::Config::captcha_seckey;
my $comment_max_length = $Blogsum::Config::comment_max_length;
my $comments_allowed = $Blogsum::Config::comments_allowed;
my $smtp_server = $Blogsum::Config::smtp_server;
my $smtp_sender = $Blogsum::Config::smtp_sender;
my $articles_per_page = $Blogsum::Config::articles_per_page;
my $google_analytics_id = $Blogsum::Config::google_analytics_id;
my $google_webmaster_id = $Blogsum::Config::google_webmaster_id;


###########################
# main execution          #
###########################
use strict;
my $cgi = CGI->new;
my $dbh = DBI->connect("DBI:SQLite:dbname=$database", '', '', { RaiseError => 1 }) || die $DBI::errstr;
my $template = HTML::Template->new(filename => $tmplfile_index, die_on_bad_params => 0);
if ($cgi->param('rss')) {
	output_rss();
} else {
	read_comment() if $comments_allowed;
	my $articles = get_articles();
	my $archives = get_archives();
	$template->param( archives => $archives );
	$template->param( title => $blog_title );
	$template->param( subtitle => $blog_subtitle );
	$template->param( copyright => $blog_rights );
	$template->param( google_analytics_id => $google_analytics_id );
	$template->param( google_webmaster_id => $google_webmaster_id );
	if (@{$articles}) {
		$template->param( articles => $articles );
	 	if ($cgi->param('uri') && $comments_allowed) {
			$template->param( comment_form => 1 );
			$template->param( comment_max_length => $comment_max_length );
			$template->param( id => $articles->[0]->{'id'} );
		}
	} else {
		$template->param( error => '404 post not found' );
	}
	print $cgi->header(), $template->output;
}
$dbh->disconnect;


###########################
# subfunctions            #
###########################

sub output_rss {

	my $version = ($cgi->param('rss') == 2) ? '2.0' : '1.0';
	my $rss = XML::RSS->new( version => $version );

	$rss->channel (
		title => $blog_title,
		link => $blog_url,
		description => $blog_subtitle,
		dc => {
			subject => $blog_title,
			creator => $blog_owner,
			publisher => $blog_owner,
			rights => $blog_rights,
			language => 'en-us',
		},
		syn => {
			updatePeriod => $feed_updates,
			updateFrequency => 1,
			updateBase => '1901-01-01T00:00+00:00',
		}
	);

	my $articles = get_articles();
	for my $item (@{$articles}) {
		$item->{'date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($item->{'year'}, $item->{'month'}) = ($1, $2);
		my $link = sprintf("%s%s/%s/%s", $blog_url, $item->{'year'}, $item->{'month'}, $item->{'uri'});

		if ($version eq '2.0') {
			$rss->add_item (
				title => $item->{'title'},
				link => $link,
				description => $item->{'body'},
				author => $item->{'author'},
				category => [split(/,/, $item->{'tags'})],
				comments => $link . '#comments',
				pubDate => POSIX::strftime("%a, %d %b %Y %H:%M:%S %Z", gmtime($item->{'epoch'})),
			);
		} else {
			$rss->add_item (
				title => $item->{'title'},
				link => $link,
				description => $item->{'body'},
				dc => {
					subject => $blog_title,
					creator => $item->{'author'},
					date => POSIX::strftime("%a, %d %b %Y %H:%M:%S %Z", gmtime($item->{'epoch'})),
				},
			);
		}
	}
	print $cgi->header('application/rss+xml'), $rss->as_string;
}

sub get_articles {

	my $page;
	my $offset;
	my $limit_clause;
	my $where_clause;
	my $j = 0;
	my $show_comments = 0;

	$articles_per_page = ($articles_per_page > 0) ? $articles_per_page : -1;
	if ($cgi->param('page') && POSIX::isdigit($cgi->param('page'))) {
		$page = $cgi->param('page');
 		$offset = ($page - 1) * $articles_per_page;
	} else {
		$page = 1;
		$offset = 0;
	}
	$limit_clause = " LIMIT $articles_per_page OFFSET $offset";

	if (($cgi->param('year') =~ /\d{4}/)&& (1900 < $cgi->param('year')) && ($cgi->param('year') < 2036)) {
		$where_clause .= 'WHERE date LIKE \'%' . $cgi->param('year');
		$j++;
		if (($cgi->param('month') =~ /\d{2}/) && (0 < $cgi->param('month')) && ($cgi->param('month') < 12)) {
			$where_clause .= '-' . $cgi->param('month') . '%\' AND enabled=1 ';
			$j++;
			if ($cgi->param('uri') =~ /\w+/) {
				$where_clause .= 'AND uri=? AND enabled=1 ';
				$limit_clause = '';
				$j++;
				$show_comments=1;
			}
		} else {
			$where_clause .= "\%' AND enabled=1 ";
		}
	} elsif ($cgi->param('search')) {
		$where_clause .= "WHERE (tags LIKE ? OR author LIKE ?) AND enabled=1 ";

	} elsif ($cgi->param('id')) {
		$where_clause .= 'WHERE id=? AND enabled=1 ';
		$limit_clause = '';
		$show_comments=1;

	} else {
		$where_clause .= 'WHERE enabled=1 ';
	}

	my $query = 'SELECT *, strftime("%s", date) AS epoch FROM articles ' . $where_clause . 'ORDER BY date DESC' . $limit_clause;
	my $sth = $dbh->prepare($query);
	
	if ($j == 3) {
		$sth->execute($cgi->param('uri')) || die $dbh->errstr;
} elsif ($cgi->param('search')) {
		my $search_tag = sprintf("%%%s%%", $cgi->param('search'));
		$sth->execute($search_tag, $search_tag) || die $dbh->errstr;
	} elsif ($cgi->param('id')) {
		$sth->execute($cgi->param('id')) || die $dbh->errstr;
	} else {
		$sth->execute() || die $dbh->errstr;
	}

	my @articles;
	while (my $result = $sth->fetchrow_hashref) {
		$result->{'date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($result->{'year'}, $result->{'month'}) = ($1, $2);
		# cut off readmore if we're on the front page
		if (($result->{'body'} =~ /<!--readmore-->/) && ($j < 3)) {
			$result->{'body'} =~ /(.*)\<\!\-\-readmore\-\-\>/s;
			$result->{'body'} = $1;
			$result->{'readmore'}++;
		}
		$result->{'tag_loop'} = format_tags($result->{'tags'}) if ($result->{'tags'});
		my $comments = get_comments(article_id => $result->{'id'}, enabled => 1);
		$result->{'comments_count'} = scalar(@{$comments});
		if ($show_comments) {
			$result->{'comments'} = $comments;
		}
		push(@articles, $result);
	}

	my $query2 = 'SELECT count(*) as total FROM articles WHERE enabled=1';
	my $sth2 = $dbh->prepare($query2);
	$sth2->execute || die $dbh->errstr;
	my $article_count = $sth2->fetchrow_hashref->{'total'};
	$template->param( page_next => ($page + 1) ) if ($article_count > ($offset + $articles_per_page));
	$template->param( page_last => ($page - 1) ) if (($page > 1) && ($article_count > $offset));

	return (\@articles);
}

sub get_archives {

	my %history;
	my @archives;
	my %months = (
			'01' => 'January',
			'02' => 'February',
			'03' => 'March',
			'04' => 'April',
			'05' => 'May',
			'06' => 'June',
			'07' => 'July',
			'08' => 'August',
			'09' => 'September',
			'10' => 'October',
			'11' => 'November',
			'12' => 'December',
	);

	my $query = 'SELECT * FROM articles WHERE enabled=1 ORDER BY date DESC';
	my $sth = $dbh->prepare($query);
	$sth->execute || die $dbh->errstr;
	while (my $result = $sth->fetchrow_hashref) {
		$result->{'date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($result->{'year'}, $result->{'month'}) = ($1, $2);
		unless ($history{$result->{'year'}}) {
			push(@archives, { year => $result->{'year'} });
			$history{$result->{'year'}}{'exists'}++;
		}
		unless ($history{$result->{'year'}}{$result->{'month'}}) {
			push(@archives, {
					year => $result->{'year'},
					month => $result->{'month'},
					month_name => $months{$result->{'month'}},
			});
			$history{$result->{'year'}}{$result->{'month'}}{'exists'}++;
		}
		my $title = my $full_title = $result->{'title'};
		#my $title = $full_title;
		if (length($title) > 28) {
			$title = substr($title, 0, 25) . '...';
		}
		push(@archives, {
				year => $result->{'year'},
				month => $result->{'month'},
				month_name => $months{$result->{'month'}},
				title => $title,
				full_title => $full_title,
				uri => $result->{'uri'},
		});
	}
	return \@archives;
}

sub format_tags {

	my $tags = shift;
	my @tags;

	foreach (split(/,/, $tags)) {
		push(@tags, { 'tag' => $_ });
	}

	return \@tags;
}

sub read_comment {

	my $captcha = Captcha::reCAPTCHA->new;
	my %friendly_errors = (
			'invalid-site-public-key'	=> "oh noes, this shouldn't happen",
			'invalid-site-private-key'	=> "oh noes, this shouldn't happen",
			'invalid-request-cookie'	=> "oh noes, this shouldn't happen",
			'verify-params-incorrect'	=> "oh noes, this shouldn't happen",
			'invalid-referrer'			=> "oh noes, this shouldn't happen",
			'recaptcha-not-reachable'	=> "oh noes, this shouldn't happen",
			'incorrect-captcha-sol'		=> "oopsie, try again",
	);

	if ($cgi->param('recaptcha_response_field') && $cgi->param('comment') && $cgi->param('id')) {

		# test our captcha
		my $result = $captcha->check_answer( $captcha_seckey, $ENV{'REMOTE_ADDR'}, $cgi->param('recaptcha_challenge_field'), $cgi->param('recaptcha_response_field') );

		if ($result->{'is_valid'}) {

			# save comment
			my $comment = HTML::Entities::encode($cgi->param('comment'));
			my $stmt = "INSERT INTO comments VALUES (NULL, ?, datetime('now'), ?, ?, ?, ?, 0)";
			my $sth = $dbh->prepare($stmt);
			my $comment_name = $cgi->param('name') ? substr($cgi->param('name'), 0, 100) : 'anonymous';
			my $comment_email = $cgi->param('email') ? substr($cgi->param('email'), 0, 100) : undef;
			my $comment_url = $cgi->param('url') ? substr($cgi->param('url'), 0, 100) : undef;
			my $comment_body = substr(HTML::Entities::encode($cgi->param('comment')), 0, $comment_max_length);
			$sth->execute($cgi->param('id'), $comment_name, $comment_email, $comment_url, $comment_body) || die $dbh->errstr;
			$template->param( message => 'comment awaiting moderation, thank you' );

			# send email notification
			my $smtp = Net::SMTP->new($smtp_server);
			$smtp->mail($ENV{USER});
			$smtp->to("$blog_owner\n");
			$smtp->data();
			$smtp->datasend("From: $smtp_sender\n"); 
			$smtp->datasend("To: $blog_owner\n");
			$smtp->datasend("Subject: $blog_title comment submission\n\n");
			$smtp->datasend("You have received a new comment submission.\n\n"); 
			$smtp->datasend(sprintf("From: %s\n", $comment_name));
			$smtp->datasend(sprintf("Date: %s\n", scalar(localtime)));
			$smtp->datasend(sprintf("Comment:\n\"%s\"\n\n", $comment_body));
			$smtp->datasend("Moderate comments at ${blog_url}admin.cgi?view=moderate\n");
			$smtp->dataend(); 
			$smtp->quit;
		} else {
			$template->param( error => $friendly_errors{ $result->{'error'} } );
			$template->param( name => $cgi->param('name') );
			$template->param( email => $cgi->param('email') );
			$template->param( url => $cgi->param('url') );
			$template->param( comment => $cgi->param('comment') );
			$template->param( id => $cgi->param('id') );
		}
	}
	# present the challenge
	#my $options = { theme => 'red' };
	#$template->param( captcha_options => $captcha->get_options_setter( $options ) );
	$template->param( captcha => $captcha->get_html( $captcha_pubkey ) );
}

sub get_comments {

	my %args = @_;

	my $query = 'SELECT * FROM comments WHERE article_id=? AND enabled=? ORDER BY date ASC';
	my $sth = $dbh->prepare($query);
	$sth->execute($args{'article_id'}, $args{'enabled'}) || die $dbh->errstr;
	my @comments;
	while (my $result = $sth->fetchrow_hashref) { 
		push(@comments, $result);
	}
	return \@comments;
}

