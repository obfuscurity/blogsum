#!/usr/bin/perl

# Blogsum
# Copyright (c) 2009 Jason Dixon <jason@dixongroup.net>
# All rights reserved.

use strict;
use DBI;
use XML::Simple;

die "Usage: wp2blogsum.pl <file.xml> <file.db>\n\n" unless (@ARGV == 2);

my $wpxml = $ARGV[0];
my $database = $ARGV[1];
my $xs = XML::Simple->new();
my $ref = $xs->XMLin($wpxml);
my $dbh = DBI->connect("DBI:SQLite:dbname=$database",'','', { RaiseError => 1 }) || die $DBI::errstr;
my $stmt = "INSERT INTO articles VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)";
my $sth = $dbh->prepare($stmt);
my $stmt2 = "INSERT INTO comments VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)";
my $sth2 = $dbh->prepare($stmt2);

foreach my $item ( @{$ref->{'channel'}->{'item'}} ) {
	next unless ($item->{'wp:post_type'} eq 'post');
	my $title = $item->{'title'};
	my $date = $item->{'wp:post_date'};
	my $uri = $item->{'wp:post_name'};
	my $author = $item->{'dc:creator'};
	my $enabled = ($item->{'wp:status'} eq 'publish') ? 1 : 0;
	my $content = $item->{'content:encoded'};
	$content =~ s///g;					# remove 
	unless (($content =~ /<pre>/) || ($content =~ <ul>) || ($content =~ <ol>)) {
		$content =~ s/<\!\-\-more\-\->/<\!\-\-readmore\-\->/mg;	# convert more to readmore
		$content =~ s/^/<p>/mg;				# add <p> to beginning of line
		$content =~ s/\r\n/<\/p>\r\n/mg;		# add </p> to end of line
		$content =~ s/$/<\/p>/mg;			# add </p> to end of story (no \r\n)
		$content =~ s/^<p><\/p>$//mg;			# remove <p></p> (empty lines)
		$content =~ s/^<p>(<\!\-\-\w+\-\->)<\/p>/$1/mg;		# remove <p></p> (comment lines)
		$content =~ s/^<\/p>$//mg;			# remove extra </p> from end of story
		$content =~ s/<p><ul>/<ul>/mg;			# remove <p> before <ul>
		$content =~ s/<ul><\/p>/<ul>/mg;		# remove </p> after <ul>
		$content =~ s/<p><\/ul>/<\/ul>/mg;		# remove <p> before </ul>
		$content =~ s/<\/ul><\/p>/<\/ul>/mg;		# remove </p> after </ul>
		$content =~ s/<p><li>/<li>/mg;			# remove <p> before <li>
		$content =~ s/<li><\/p>/<li>/mg;		# remove </p> after <li>
		$content =~ s/<p><\/li>/<\/li>/mg;		# remove <p> before </li>
		$content =~ s/<\/li><\/p>/<\/li>/mg;		# remove </p> after </li>
	}
	my @tags;
	if ($item->{'category'}) {
		for my $category (@{$item->{'category'}}) {
			if (ref($category) eq 'HASH') {
				if ($category->{'nicename'}) {
					push(@tags, $category->{'content'});
				}
			}
		}
	}
	$sth->execute($date, $title, $uri, $content, join(',', @tags), $enabled, $author) || die $dbh->errstr;
	my $article_id = $dbh->func('last_insert_rowid');
	if ($item->{'wp:comment'}) {
		if (ref($item->{'wp:comment'}) eq 'ARRAY') {
			for my $comment (@{$item->{'wp:comment'}}) {
				$sth2->execute($article_id, $comment->{'wp:comment_date'}, $comment->{'wp:comment_author'}, $comment->{'wp:comment_author_email'}, $comment->{'wp:comment_author_url'}, $comment->{'wp:comment_content'}, $comment->{'wp:comment_approved'}) || die $dbh->errstr;
			}
		} else {
			my $comment = $item->{'wp:comment'};
			$sth2->execute($article_id, $comment->{'wp:comment_date'}, $comment->{'wp:comment_author'}, $comment->{'wp:comment_author_email'}, $comment->{'wp:comment_author_url'}, $comment->{'wp:comment_content'}, $comment->{'wp:comment_approved'}) || die $dbh->errstr;
		}
	}
}

$dbh->disconnect;


