# encoding: utf-8
import httmock


def only_httmock(*mocks):
    """
    Wraps a typical HTTPMock context manager to raise an error if no mocks match.
    """
    mocks = mocks + (fail_everything_else,)
    return httmock.HTTMock(*mocks)


TEST_FKEY = 'dc63b60f5ada11372b8ff63821d9bf24'


@httmock.urlmatch(path=r'^/chats/join/favorite$')
def favorite_with_test_fkey(url, request):
    return '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>


    <link rel="stylesheet" href="http://cdn-chat.sstatic.net/chat/css/chat.stackexchange.com.css?v=267360bbdcd6">
    <link rel="shortcut icon" href="http://cdn.sstatic.net/stackexchange/img/favicon.ico?v=c3"><link rel="apple-touch-icon" href="http://cdn.sstatic.net/stackexchange/img/apple-touch-icon.png?v=c3"><link rel="search" type="application/opensearchdescription+xml" title="Chat for chat.stackexchange.com" href="/opensearch.xml">                    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>

    <script type="text/javascript" src="http://cdn-chat.sstatic.net/chat/js/master.js?v=0a552f322230"></script>

<script type="text/javascript">
    function IMAGE(f) { return ("http://cdn-chat.sstatic.net/chat/img/" + f); }
</script>


    <script type="text/javascript">$(function() {
        var pagesupport = initBasicPage("The Stack Exchange Network",20,null,false);moderatorTools(pagesupport.notify).initFlagSupport(false, 1251);});

    var inboxUnviewedCount = -1;
    $(function () { genuwine.init("851"); })

    </script>

</head>
<body class="outside">


    <div id="container">



<link rel="stylesheet" type="text/css" href="http://cdn.sstatic.net/skins/topbar/topbar.css"/>
<div class="topbar">
    <div class="topbar-wrapper">

        <div class="js-topbar-dialog-corral">
        </div>

        <div class="network-items">

            <a href="http://stackexchange.com"
               class="topbar-icon icon-site-switcher yes-hover js-site-switcher-button js-gps-track"
               data-gps-track="site_switcher.show"
               title="A list of all 123 Stack Exchange sites">
                <span class="hidden-text">Stack Exchange</span>
            </a>

                <a href="#"
                   class="topbar-icon icon-inbox yes-hover js-inbox-button"
                   title="Recent inbox messages">
                    <span class="hidden-text">Inbox</span>
                    <span class="unread-count" style="display:none"></span>
                </a>
                                        <a href="#"
                               class="topbar-icon icon-achievements yes-hover js-achievements-button"
                               data-unread-class="icon-achievements-unread"
                               title="Recent achievements: reputation, badges, and privileges earned">
                                <span class="hidden-text">Reputation and Badges</span>
                                <span class="unread-count" style="display:none"></span>
                            </a>
        </div>
        <div class="topbar-links">
                <div class="links-container">
                    <span class="topbar-menu-links">
<a href="/users/1251/jeremy-banks-" title="Jeremy Banks Ψ">Jeremy Banks Ψ</a>
                                            </span>
                </div>
                <div class="search-container">
                    <form action="/search" method="get" autocomplete="off">
                        <input name="q" id="searchbox" type="text" placeholder="search" size="28" maxlength="80" />
                    </form>
                </div>
        </div>
    </div>
</div>
<script src="http://cdn-chat.sstatic.net/chat/js/third-party/jquery.typewatch.js?v=b955aea06af0"></script>
<script src="http://cdn-chat.sstatic.net/chat/js/topbar.js?v=7c120f36aad4"></script>
<script>
        $(function() {
            StackExchange.topbar.init({"serverTime":1398621212,"enableLogging":false});
        });
</script>

                <div id="header">
                        <div id="hlogo">
                            <div id="header-logo">    <a title="The Stack Exchange Network" href="http://stackexchange.com"><img src="http://cdn-chat.sstatic.net/chat/img/se-chat-logo.png?v=c40d0fda6c03" alt="The Stack Exchange Network"/></a>
</div>
                        </div>
                        <div id="hmenu">
                            <div class="nav">
                                <ul>
                                    <li >
                                        <a href="/users" title="107 users active in the last 60 minutes">users (107)</a>
                                    </li>
                                    <li >
                                        <a href="/rooms" title="50 rooms active in the last 120 minutes">rooms (50)</a>
                                    </li>
                                    <li >
                                        <a href="/faq">faq</a>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>


        <div id="content">


    <h2>Join</h2>
    Please confirm that you wish to rejoin your favorited rooms:
    <form method="post" action="">
        <input id="fkey" name="fkey" type="hidden" value="''' + TEST_FKEY + '''" />
        <input class="button" type="submit" value="join" />
    </form>

        </div>
    </div>
    <div id="footer">
        <div class="footerwrap">
            <div id="footer-menu">
                <a href="/faq">faq</a> |
                <a href="http://stackexchange.com/legal">legal</a> |
                <a href="http://stackexchange.com/legal/privacy-policy">privacy policy</a> |
                <a class="mobile-on" href="#">mobile</a>
            </div>
            <div id="copyright">
                site design / logo &copy; 2014 stack exchange, inc
            </div>
        </div>
    </div>
</body>
</html>'''


@httmock.urlmatch(netloc=r'.*')
def fail_everything_else(url, request):
    raise Exception("unexpected request; no mock available", request)
