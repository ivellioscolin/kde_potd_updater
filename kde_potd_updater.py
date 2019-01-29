import urllib.request, urllib.parse
import re, os, sys, tempfile, string, random, shutil, datetime, copy

WALLPAPER_DIR = os.environ['HOME'] + "/.cache/plasmashell/plasma_engine_potd/"
SCREEN_LOCKER_DIR = os.environ['HOME'] + "/.cache/kscreenlocker_greet/plasma_engine_potd/"

TARGET_DIR = [WALLPAPER_DIR, SCREEN_LOCKER_DIR]

class POTDProvider:
    def __init__(self, name, url, desc):
        self.name = name
        self.url = url
        self.desc = desc

POTD_LIST = []
POTD_LIST.append(POTDProvider("apod", "https://apod.nasa.gov/apod", "Astronomy Picture of the Day"))
POTD_LIST.append(POTDProvider("bing", "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1", "Bing's Picture of the Day"))
POTD_LIST.append(POTDProvider("epod", "https://epod.usra.edu/", "Earth Science Picture of the Day"))
POTD_LIST.append(POTDProvider("flickr", "https://api.flickr.com/services/rest/", "Flickr Picture of the Day"))
POTD_LIST.append(POTDProvider("natgeo", "http://www.nationalgeographic.com/photography/photo-of-the-day/", "National Geographic"))
POTD_LIST.append(POTDProvider("noaa", "http://www.nesdis.noaa.gov/content/imagery-and-data", "NOAA Environmental Visualization Laboratory Picture of the Day"))
POTD_LIST.append(POTDProvider("wcpotd", "https://commons.wikimedia.org/w/api.php", "Wikimedia Picture of the Day"))

def send_url_req(potd):
    req_content = ""
    req = urllib.request.Request(potd.url)
    try:
        response = urllib.request.urlopen(req)
    except urllib.request.HTTPError as err:
        print("(HTTPError %d) %s:%s" %(err.code, potd.name, potd.url))
    else:
        req_content = response.read().decode("utf-8", errors='ignore')

    return req_content

def download_from_url(url, filename):
    is_ok = False
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
    except urllib.request.HTTPError as err:
        print("(HTTPError %d) when downloading %s" %(err.code, url))
    else:
        f = open(filename, "wb")
        f.write(response.read())
        f.close()
        is_ok = True

    return is_ok

def show_help():
    print("\nKDE Plasma POTD Updater\n")
    print("Supported POTD provider:")
    potds = ""
    for p in POTD_LIST:
        print("- %s: %s\n    %s" %(p.name, p.desc, p.url))
        potds += p.name
        if (POTD_LIST.index(p) < len(POTD_LIST) - 1):
            potds += "|"
    print("\nUsage: python kde_potd_updater.py %s\n" %(potds))

def update_service_apod(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"img src=\"(.+)\"", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
            is_ok = download_from_url(img_url, target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_bing(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"^.*\"url\":\"([^\"]+)\".*$", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
            is_ok = download_from_url(img_url, target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_epod(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        pattern = r"class=\"asset-img-link\" href=\"(%s.a/.+-pi)" %(potd.url)
        imgs = re.findall(pattern, page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
            is_ok = download_from_url(img_url, target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_flickr(potd, target_file):
    is_ok = False
    potd_api = copy.copy(potd)
    date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(1), '%Y-%m-%d')
    flickr_api = "?api_key=11829a470557ad8e10b02e80afacb3af"
    flickr_api += "&method=flickr.interestingness.getList"
    flickr_api += "&date=%s" %(date)
    flickr_api += "&extras=url_o"
    flickr_api += "&page=1"
    flickr_api += "&per_page=1"
    potd_api.url = urllib.parse.urljoin(potd.url, flickr_api)
    page_content = send_url_req(potd_api)
    if (page_content):
        imgs = re.findall(r"url_o=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            is_ok = download_from_url(imgs[len(imgs) - 1], target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_natgeo(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"<meta property=\"og:image\" content=\"(.+)\"", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
            is_ok = download_from_url(img_url, target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))
    
    return is_ok

def update_service_noaa(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"img alt=\"Latest Image of the Day.*src=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
            is_ok = download_from_url(img_url, target_file)
        else:
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_wcpotd(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    potd_api = copy.copy(potd)
    wikimedia_api = "?action=parse"
    wikimedia_api += "&text={{Potd}}"
    wikimedia_api += "&contentmodel=wikitext"
    wikimedia_api += "&prop=text"
    wikimedia_api += "&format=json"
    potd_api.url = urllib.parse.urljoin(potd.url, wikimedia_api)
    page_content = send_url_req(potd_api)
    if (page_content):
        imgs = re.findall(r"^.*Commons:Picture of the day.*?href=\\\"([^\"]*)\\\"", page_content, flags=re.IGNORECASE)
        img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
        potd_api.url = urllib.parse.urljoin(potd.url, img_url)
        page_content = send_url_req(potd_api)
        if (page_content):
            imgs = re.findall(r"fullImageLink.*?href=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
            if (len(imgs)):
                is_ok = download_from_url(imgs[len(imgs) - 1], target_file)
            else:
                print("Can't parse image for %s:%s" %(potd.name, potd.url))
        else:
            print("Can't parse page for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_potd(potd):
    tmp_file = os.path.join(tempfile.gettempdir(), ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)))
    potd_provide_callback = "update_service_" + potd.name
    if hasattr(sys.modules[__name__], potd_provide_callback):
        print("Updating %s ..." %(potd.desc))
        is_ok = getattr(sys.modules[__name__], potd_provide_callback)(potd, tmp_file)
        if (is_ok):
            for targ in TARGET_DIR:
                targ_file = os.path.join(targ, potd.name)
                shutil.copyfile(tmp_file, targ_file)
            os.remove(tmp_file)
    else:
        print("%s doesn't have a service" %(potd.name))

def main():
    if(len(sys.argv) == 2):
        for p in POTD_LIST:
            if (sys.argv[1] == p.name):
                update_potd(p)
                return
        print("\nUnknown POTD provider \"%s\"" %(sys.argv[1]))
        show_help()
    else:
        show_help()

if __name__== "__main__":
    main()