BEGIN TRANSACTION;
CREATE TABLE articles (id integer primary key, date date, title text, uri text, body text, tags text, enabled boolean, author text);
INSERT INTO "articles" VALUES(1,'2009-11-16 18:07:10','Welcome to Blogsum','Welcome-to-Blogsum','<h3>Introduction</h3>

<p>Blogsum is a very basic blogging application. It was written from scratch with a focus on simplicity and security, favoring practicality over feature bloat.</p>

<h3>Writing Articles</h3>

<p>The Administration interface is straightforward and bereft of unnecessary features.  Three views allow you to <a href="/admin.cgi?view=edit">create</a> posts, <a href="/admin.cgi?view=moderate">moderate</a> comments and <a href="/admin.cgi">administrate</a> (manage posts). Blogsum uses HTML markup for article formatting.  New articles are saved as a <em>draft</em> <img align="absmiddle" src="/themes/default/images/draft.gif">.</p>

<p>There''s one other useful thing to remember about editing your articles. If you have a lengthy post you might want to split it up with the <b><tt>&lt;!--readmore--&gt;</tt></b> tag.  Anything that appears after this HTML comment will appear in the full article view, but will be hidden from your blog''s front page.  Here comes one now...</p>

<!--readmore-->

<h3>Managing Articles</h3>

<p>As mentioned above, new articles are saved as a draft.  Click the <em>publish</em> <img align="absmiddle" src="/themes/default/images/play.gif"> button to see your post go live.  You can make <em>edits</em> <img align="absmiddle" src="/themes/default/images/plus.gif"> to a live article, but the timestamp won''t be updated unless you re-draft and re-publish the story. If you decide that you really want to remove an article from the administrate view, you can <em>delete</em> <img align="absmiddle" src="/themes/default/images/delete.gif"> it.</p>

<h3>Comments and Moderation</h3>

<p>Article comments are moderated and must be accompanied with a successful Captcha challenge. All user input is encoded to avoid XSS issues.  Click on the <em>moderate</em> view to <em>approve</em> <img align="absmiddle" src="/themes/default/images/check.gif"> or <em>deny</em> <img align="absmiddle" src="/themes/default/images/delete.gif"> a comment submission.</p>

<h3>Using Tags</h3>

<p>Tags are used liberally throughout Blogsum.  Besides the tags defined in an article, Blogsum also uses the <tt>/Tags/</tt> path to search for authors.  It also favors the use of tags as a conventional replacement to <em>categories</em>.  Anyone can use the <tt>/Tags/</tt> path to search for articles in Blogsum (<a href="/Tags/jdixon">example</a>).</p>

<h3>Themes</h3>

<p>Blogsum includes a default theme (what you''re viewing now).  If you wish to modify it according to your tastes, you should create your own theme. To create a theme, copy the <tt>themes/default</tt> directory to your own directory (e.g. <tt>themes/foobar</tt>) and modify accordingly. Changes can be made to any of the files in a theme, but the path and filenames should not change. When you are finished, edit the <tt>$blog_theme</tt> setting in <tt>Blogsum/Config.pm</tt> and restart your webserver.</p>

<h3>Go Forth and Blog!</h3>

<p>As you can see, Blogsum is a very simple application designed for <b><em>less maintenance, more writing</em></b>. We hope you enjoy publishing your works within Blogsum. If you create your own themes, please consider donating those back to the <a href="http://blogsum.obfuscurity.com/">project</a>. Enjoy!</p>
','Blogsum,Welcome',1,'jdixon');
CREATE TABLE comments (id integer primary key, article_id integer, date date, name text, email text, url text, comment text, enabled boolean);
COMMIT;
