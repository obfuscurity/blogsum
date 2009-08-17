
# Blogsum
# Copyright (c) 2009 Jason Dixon <jason@dixongroup.net>
# All rights reserved.


###########################
# user options            #
###########################
my $database = 'data/site.db';
my $tmplfile = 'templates/index.html';
my $blog_title = 'example.com';
my $blog_url = 'http://www.example.com/';
my $feed_motto = 'My New Blog';
my $feed_owner = 'user@example.com';
my $feed_rights = 'Copyright 2009, Example User';
my $feed_updates = 'hourly';
my $captcha_pubkey = '';
my $captcha_seckey = '';
my $comment_max_length = '1000';


###########################
# main execution          #
###########################
my $cgi = CGI->new;
my $dbh = DBI->connect("DBI:SQLite:dbname=$database", '', '', { RaiseError => 1 }) || die $DBI::errstr;
my $template = HTML::Template->new(filename => $tmplfile, die_on_bad_params => 0);
if ($cgi->param('rss1')) {
	output_rss();
} else {
	read_comment();
	my $articles = get_articles();
	my $archives = get_archives();
	$template->param(archives => $archives);
	$template->param( title => $blog_title );
	if (@{$articles}) {
		$template->param( articles => $articles );
	 	if ($cgi->param('uri')) {
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

	my $rss = XML::RSS->new( version => '1.0' );

	$rss->channel (
		title => $blog_title,
		link => $blog_url,
		description => $feed_motto,
		dc => {
			subject => $blog_title,
			creator => $feed_owner,
			publisher => $feed_owner,
			rights => $feed_rights,
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
		$rss->add_item (
			title => $item->{'title'},
			link => sprintf("%s%s/%s/%s", $blog_url, $item->{'year'}, $item->{'month'}, $item->{'uri'}),
			description => $item->{'body'},
			dc => {
				subject => $blog_title,
				creator => $item->{'author'},
				date => $item->{'date'},
			},
		);
	}
	print $cgi->header('application/rss+xml'), $rss->as_string;
}

sub get_articles {

	my $criteria;
	my $c=0;
	my $show_comments=0;

	if (($cgi->param('year') =~ /\d{4}/)&& (1900 < $cgi->param('year')) && ($cgi->param('year') < 2036)) {
		$criteria .= 'WHERE date LIKE \'%' . $cgi->param('year');
		$c++;
		if (($cgi->param('month') =~ /\d{2}/) && (0 < $cgi->param('month')) && ($cgi->param('month') < 12)) {
			$criteria .= '-' . $cgi->param('month') . '%\' AND enabled=1 ';
			$c++;
			if ($cgi->param('uri') =~ /\w+/) {
				$criteria .= 'AND uri=? AND enabled=1 ';
				$c++;
				$show_comments=1;
			}
		} else {
			$criteria .= "\%' AND enabled=1 ";
		}
	} elsif ($cgi->param('search')) {
		$criteria .= "WHERE tags LIKE ? AND enabled=1 ";
	} elsif ($cgi->param('id')) {
		$criteria .= 'WHERE id=? AND enabled=1 ';
		$show_comments=1;
	} else {
		$criteria .= 'WHERE enabled=1 ';
	}

	my $query = 'SELECT * FROM articles ' . $criteria . 'ORDER BY date DESC';
	my $sth = $dbh->prepare($query);
	
	if ($c == 3) {
		$sth->execute($cgi->param('uri')) || die $dbh->errstr;
	} elsif ($cgi->param('search')) {
		$sth->execute(sprintf("%%%s%%", $cgi->param('search'))) || die $dbh->errstr;
	} elsif ($cgi->param('id')) {
		$sth->execute($cgi->param('id')) || die $dbh->errstr;
	} else {
		$sth->execute() || die $dbh->errstr;
	}

	my @articles;
	while (my $result = $sth->fetchrow_hashref) {
		$result->{'date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($result->{'year'}, $result->{'month'}) = ($1, $2);
		$result->{'tag_loop'} = format_tags($result->{'tags'}) if ($result->{'tags'});
		if ($show_comments) {
			$result->{'comments'} = get_comments(article_id => $result->{'id'}, enabled => 1);
		}
		push(@articles, $result);
	}
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
			my $comment = $cgi->param('comment');
			$comment = HTML::Entities::encode($text);
			my $stmt = "INSERT INTO comments VALUES (NULL, ?, datetime('now'), ?, ?, ?, ?, 0)";
			my $sth = $dbh->prepare($stmt);
			$sth->execute($cgi->param('id'), $cgi->param('name') || 'anonymous', $cgi->param('email') || undef, $cgi->param('url') || undef, substr(HTML::Entities::encode($cgi->param('comment')), 0, $comment_max_length)) || die $dbh->errstr;
			$template->param( message => 'comment awaiting moderation, thank you' );
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
	my $query = 'SELECT * FROM comments WHERE article_id=? AND enabled=? ORDER BY date DESC';
	my $sth = $dbh->prepare($query);

	$sth->execute($args{'article_id'}, $args{'enabled'}) || die $dbh->errstr;
	my @comments;
	while (my $result = $sth->fetchrow_hashref) { 
		push(@comments, $result);
	}
	return \@comments;
}

