
# Blogsum
# Copyright (c) 2009 Jason Dixon <jason@dixongroup.net>
# All rights reserved.

###########################
# pragmas and vars        #
###########################
use strict;
use Blogsum::Config;
my $database = $Blogsum::Config::database;
my $blog_theme = $Blogsum::Config::blog_theme;
my $blog_title = $Blogsum::Config::blog_title;


###########################
# main execution          #
###########################
my $cgi = CGI->new;
my $dbh = DBI->connect("DBI:SQLite:dbname=$database", '', '', { RaiseError => 1 }) || die $DBI::errstr;
my $template = HTML::Template->new(filename => "themes/${blog_theme}/admin.tmpl", die_on_bad_params => 0);
$template->param( theme => $blog_theme );
my $view;

if ($cgi->param('view')) {
	if ($cgi->param('view') eq 'moderate') {
		$view = 'moderate';
		manage_comments();
	} elsif ($cgi->param('view') eq 'edit') {
		$view = 'create';
		edit_article();
	} else {
		$view = 'administrate';
		manage_articles();
	}
} else {
	$view = 'administrate';
	manage_articles();
}

$dbh->disconnect;


###########################
# subfunctions            #
###########################

sub manage_articles {

	my $article_id;
	my $status=2;

	if ($cgi->param('delete') =~ /\d+/) {
		$article_id = $cgi->param('delete');
		$status=-1;
	}
	if ($cgi->param('draft') =~ /\d+/) {
		$article_id = $cgi->param('draft');
		$status=0;
	}
	if ($cgi->param('publish') =~ /\d+/) {
		$article_id = $cgi->param('publish');
		$status=1;
	}
	if ($status < 2) {
		my $stmt = "UPDATE articles SET enabled=? WHERE id=?";
		my $sth = $dbh->prepare($stmt);
		$sth->execute($status, $article_id) || die $dbh->errstr;
	}
	if ($status == 1) {
		my $stmt = "UPDATE articles SET date = datetime('now', 'localtime') WHERE id=?";
		my $sth = $dbh->prepare($stmt);
		$sth->execute($article_id) || die $dbh->errstr;
	}

	if (@{get_comments()} > 0) {
		$template->param( comments_to_moderate => 1);
	}
	$template->param( view => $view, blog_title => $blog_title, articles => get_articles() );
	print $cgi->header(), $template->output;
}

sub manage_comments {

	my $comment_id;
	my $status=2;

	if ($cgi->param('delete') =~ /\d+/) {
		$comment_id = $cgi->param('delete');
		$status=-1;
	}
	if ($cgi->param('publish') =~ /\d+/) {
		$comment_id = $cgi->param('publish');
		$status=1;
	}
	if ($status < 2) {
		my $stmt = "UPDATE comments SET enabled=? WHERE id=?";
		my $sth = $dbh->prepare($stmt);
		$sth->execute($status, $comment_id) || die $dbh->errstr;
	}

	$template->param( view => $view, blog_title => $blog_title, comments => get_comments() );
	print $cgi->header(), $template->output;
}

sub edit_article {

	# preview, pass through all input
	if ($cgi->param('preview')) {
		my $uri = $cgi->param('uri') || $cgi->param('title') || undef;
		$uri =~ s/\ /\-/g if ($uri);
		$template->param( view => $view, blog_title => $blog_title, preview => 1, edit => 1 );
		$template->param( id => $cgi->param('id') ) if ($cgi->param('id'));
		$template->param( title => $cgi->param('title') ) if ($cgi->param('title'));
		$template->param( uri => $uri ) if ($uri);
		$template->param( preview => $cgi->param('body') ) if ($cgi->param('body'));
		$template->param( body => HTML::Entities::encode($cgi->param('body')) ) if ($cgi->param('body'));
		$template->param( tags => $cgi->param('tags') ) if ($cgi->param('tags'));
		print $cgi->header(), $template->output;

	# save edits, with id (update)
	} elsif ($cgi->param('save') && $cgi->param('id')) {
		if ($cgi->param('title') && $cgi->param('uri') && $cgi->param('body')) {
			my $uri = $cgi->param('uri');
			$uri =~ s/\ /\-/g;
			my $stmt = "UPDATE articles SET title=?, uri=?, body=?, tags=? WHERE id=?";
			my $sth = $dbh->prepare($stmt);
			$sth->execute($cgi->param('title'), $uri, $cgi->param('body'), $cgi->param('tags'), $cgi->param('id')) || die $dbh->errstr;
			manage_articles();
		# if missing data, push back to preview
		} else {
			$template->param( error => 'required fields: title, uri, body' );
			$template->param( view => $view, blog_title => $blog_title, edit => 1 );
			$template->param( id => $cgi->param('id') ) if ($cgi->param('id'));
			$template->param( title => $cgi->param('title') ) if ($cgi->param('title'));
			$template->param( uri => $cgi->param('uri') ) if ($cgi->param('uri'));
			$template->param( preview => $cgi->param('body') ) if ($cgi->param('body'));
			$template->param( body => HTML::Entities::encode($cgi->param('body')) ) if ($cgi->param('body'));
			$template->param( tags => $cgi->param('tags') ) if ($cgi->param('tags'));
			print $cgi->header(), $template->output;
		}

	# save new, no id (insert)
	} elsif ($cgi->param('save')) {
		if ($cgi->param('title') && $cgi->param('body')) {
			my $uri = $cgi->param('uri') || $cgi->param('title');
			$uri =~ s/\ /\-/g;
			my $author = $ENV{'REMOTE_USER'} || 'author';
			my $stmt = "INSERT INTO articles VALUES (NULL, datetime('now', 'localtime'), ?, ?, ?, ?, 0, ?)";
			my $sth = $dbh->prepare($stmt);
			$sth->execute($cgi->param('title'), $uri, $cgi->param('body'), $cgi->param('tags'), $author) || die $dbh->errstr;
			manage_articles();
		# if missing data, push back to preview
		} else {
			$template->param( error => 'required fields: title, body' );
			$template->param( view => $view, blog_title => $blog_title, edit => 1 );
			$template->param( id => $cgi->param('id') ) if ($cgi->param('id'));
			$template->param( title => $cgi->param('title') ) if ($cgi->param('title'));
			$template->param( uri => $cgi->param('uri') ) if ($cgi->param('uri'));
			$template->param( preview => $cgi->param('body') ) if ($cgi->param('body'));
			$template->param( body => HTML::Entities::encode($cgi->param('body')) ) if ($cgi->param('body'));
			$template->param( tags => $cgi->param('tags') ) if ($cgi->param('tags'));
			print $cgi->header(), $template->output;
		}

	# edit an existing
	} elsif ($cgi->param('id')) {
		my $query = "SELECT * FROM articles WHERE id=?";
		my $sth = $dbh->prepare($query);
		$sth->execute($cgi->param('id')) || die $dbh->errstr;
		my $result = $sth->fetchrow_hashref;
		if ($result) {
			$template->param( view => $view, blog_title => $blog_title, edit => 1 );
			$template->param( preview => $result->{'body'} );
			$result->{'body'} = HTML::Entities::encode($result->{'body'});
			$template->param( $result );
			print $cgi->header(), $template->output;
		} else {
			$template->param( error => 'no results found' );
			manage_articles();
		}

	# brand new, show form
	} else {
		$template->param( view => $view, blog_title => $blog_title, edit => 1 );
		print $cgi->header(), $template->output;
	}
}

sub get_articles {

	my $query = 'SELECT * FROM articles WHERE enabled !=-1 ORDER BY date DESC';
	my $sth = $dbh->prepare($query);
	$sth->execute() || die $dbh->errstr;

	my @articles;
	while (my $result = $sth->fetchrow_hashref) {
		$result->{'date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($result->{'year'}, $result->{'month'}) = ($1, $2);
		$result->{'date'} =~ s/(\d{4}\-\d{2}\-\d{2}) \d{2}\:\d{2}\:\d{2}/$1/;
		delete $result->{'enabled'} if ($result->{'enabled'} == 0);
		$result->{'theme'} = $blog_theme;
		push(@articles, $result);
	}

	return \@articles;
}

sub get_comments {

	my $query = 'SELECT a.title AS article_title, a.uri AS article_uri, a.date AS article_date, c.* FROM articles a, comments c WHERE a.id=c.article_id AND c.enabled=0 ORDER BY c.date DESC';
	my $sth = $dbh->prepare($query);
	$sth->execute() || die $dbh->errstr;

	my @comments;
	while (my $result = $sth->fetchrow_hashref) {
		$result->{'article_date'} =~ /(\d{4})\-(\d{2})\-\d{2} \d{2}\:\d{2}\:\d{2}/;
		($result->{'article_year'}, $result->{'article_month'}) = ($1, $2);
		$result->{'theme'} = $blog_theme;
		push(@comments, $result);
	}

	return \@comments;
}


