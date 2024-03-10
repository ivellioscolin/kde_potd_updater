import urllib.request, urllib.parse
import re, os, sys, tempfile, string, random, shutil, datetime, copy
import hashlib

FLICKR_PROVIDE_CONF = "https://autoconfig.kde.org/potd/flickrprovider.conf"

POTD_DIR = os.environ['HOME'] + "/.cache/plasma_engine_potd/"

TARGET_DIR = [POTD_DIR]

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
POTD_LIST.append(POTDProvider("spotlight", "https://windows10spotlight.com/", "Windows Spotlight"))

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
    print("\nUsage: python kde_potd_updater.py %s [backup dir] [backup file surfix]\n" %(potds))
    print("Example: python kde_potd_updater.py apod /home/user/ 20200101\n")

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
    pattern = []
    pattern.append(r"class=\"asset-img-link\" href=\"(%s.a/.+-pi)" %(potd.url))
    pattern.append(r"href=\"(.*-pi)\".*")
    if (page_content):
        for p in pattern:
            imgs = re.findall(p, page_content, flags=re.IGNORECASE)
            if (len(imgs)):
                img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
                is_ok = download_from_url(img_url, target_file)
                if (is_ok):
                    break
        if (not is_ok):
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_service_flickr(potd, target_file):
    is_ok = False
    potd_api = copy.copy(potd)

    req_content = ""
    req = urllib.request.Request(FLICKR_PROVIDE_CONF)
    try:
        response = urllib.request.urlopen(req)
    except urllib.request.HTTPError as err:
        print("(HTTPError %d) %s:%s" %(err.code, "Flickr Provider Conf", FLICKR_PROVIDE_CONF))
    else:
        req_content = response.read().decode("utf-8", errors='ignore')
    api_key = re.findall(r"API_KEY=(.*)", req_content, flags=re.IGNORECASE)[0]
    api_secret = re.findall(r"API_SECRET=(.*)", req_content, flags=re.IGNORECASE)[0]

    #flickr_api = "?api_key=11829a470557ad8e10b02e80afacb3af"
    #flickr_api = "?api_key=5f412b6f21aa9b6978c979c1ca806375"
    flickr_api = "?api_key={}".format(api_key)
    flickr_api += "&method=flickr.interestingness.getList"
    flickr_api += "&extras=url_o,url_k,url_h"
    flickr_api += "&page=1"
    flickr_api += "&per_page=1"
    day_before = 0
    day_max = 30
    while True:
        if (day_before > day_max):
            print("No interesting photos within latest %d days" %(day_max))
            break
        date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(day_before), '%Y-%m-%d')
        day_before += 1
        flickr_api_date = flickr_api + "&date=%s" %(date)
        potd_api.url = urllib.parse.urljoin(potd.url, flickr_api_date)
        page_content = send_url_req(potd_api)
        if (page_content):
            err = re.findall(r"[\s\S]*?stat=\"([^\"]*?)\"[\s\S]*?msg=\"([^\"]*?)\"", page_content, flags=re.IGNORECASE)
            if (len(err)):
                print("Fail at %s" %(potd_api.url))
                print("stat: (%s) msg: (%s)" %(err[0][0], err[0][1]))
            else:
                is_ok = False
                imgs = re.findall(r"url_o=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
                if (not is_ok and len(imgs)):
                    is_ok = download_from_url(imgs[len(imgs) - 1], target_file)
                imgs = re.findall(r"url_k=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
                if (not is_ok and len(imgs)):
                    is_ok = download_from_url(imgs[len(imgs) - 1], target_file)
                imgs = re.findall(r"url_h=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
                if (not is_ok and len(imgs)):
                    is_ok = download_from_url(imgs[len(imgs) - 1], target_file)
                if (is_ok):
                    break
                else:
                    print("Can't find original/large 2048/large 1600 image for %s:%s" %(potd.name, potd.url))
    if (not is_ok):
        print("Can't find suitable image within %d days" %(day_max))

    return is_ok

def update_service_natgeo(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        pattern = []
        pattern.append(r"property=\"og:image\" content=\"(.*?)\"")
        for p in pattern:
            imgs = re.findall(p, page_content, flags=re.IGNORECASE)
            if (len(imgs)):
                img_url = urllib.parse.urljoin(domain, imgs[len(imgs) - 1])
                is_ok = download_from_url(img_url, target_file)
                if (is_ok):
                    break
        if (not is_ok):
            print("Can't parse image for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse page for %s:%s" %(potd.name, potd.url))
    
    return is_ok

def update_service_noaa(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"img alt=\"Latest Image of the Day[\s\S]*?src=\"([^\"]*)\"", page_content, flags=re.IGNORECASE)
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

def update_service_spotlight(potd, target_file):
    is_ok = False
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(potd.url))
    page_content = send_url_req(potd)
    if (page_content):
        imgs = re.findall(r"<a href=\"https://windows10spotlight.com/images/([\S]*)\"", page_content, flags=re.IGNORECASE)
        if (len(imgs)):
            page_content = ""
            img_page_url = urllib.parse.urljoin('https://windows10spotlight.com/images/', imgs[0])
            req = urllib.request.Request(img_page_url)
            try:
                response = urllib.request.urlopen(req)
            except urllib.request.HTTPError as err:
                print("(HTTPError %d) %s" %(err.code, img_page_url))
            else:
                page_content = response.read().decode("utf-8", errors='ignore')

            if (page_content):
                pattern="\"image\":\{\"@type\":\"ImageObject\",\"@id\":\"%s#primaryimage\",\"url\":\"([\S])\"" % img_page_url
                imgs = re.findall(r"\"image\":{\"@type\":\"ImageObject\",\"@id\":\"%s#primaryimage\",\"url\":\"([\S]*?)\"" % img_page_url, page_content, flags=re.IGNORECASE)
                if (len(imgs)):
                    is_ok = download_from_url(imgs[0], target_file)
                else:
                    print("Can't parse image for %s:%s" %(potd.name, potd.url))
            else:
                print("Can't parse image page for %s:%s" %(potd.name, potd.url))
        else:
            print("Can't parse page (no images) for %s:%s" %(potd.name, potd.url))
    else:
        print("Can't parse domain page for %s:%s" %(potd.name, potd.url))

    return is_ok

def update_potd(potd):
    tmp_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    tmp_file = os.path.join(tempfile.gettempdir(), tmp_name)
    potd_provide_callback = "update_service_" + potd.name
    if hasattr(sys.modules[__name__], potd_provide_callback):
        print("Processing %s ..." %(potd.desc))
        is_ok = getattr(sys.modules[__name__], potd_provide_callback)(potd, tmp_file)
        if (is_ok):
            # Save to backup dir
            if (os.path.isdir(BACKUP_DIR)):
                targ_file = os.path.join(BACKUP_DIR, potd.name+FILE_SURFIX)
                if (os.path.exists(targ_file)):
                    old_hash = 0
                    new_hash = 0
                    with open(targ_file, 'rb') as afile:
                        buf = afile.read()
                        hasher = hashlib.md5()
                        hasher.update(buf)
                        old_hash = hasher.hexdigest()
                    with open(tmp_file, 'rb') as afile:
                        buf = afile.read()
                        hasher = hashlib.md5()
                        hasher.update(buf)
                        new_hash = hasher.hexdigest()
                    if (new_hash != old_hash):
                        targ_file = targ_file + tmp_name
                        shutil.copyfile(tmp_file, targ_file)
                else:
                    shutil.copyfile(tmp_file, targ_file)
                    print("  Saved in %s for backup" %(BACKUP_DIR))

            # Save plasma wallpaper and screenlocker
            for targ in TARGET_DIR:
                if (os.path.isdir(targ)):
                    targ_file = os.path.join(targ, potd.name)
                    shutil.copyfile(tmp_file, targ_file)
                    print("  Saved in %s" %(targ))
                else:
                    print("Path %s doesn't exist" %(targ))
            os.remove(tmp_file)
    else:
        print("%s doesn't have a service" %(potd.name))

def main():
    global BACKUP_DIR
    global FILE_SURFIX
    if(len(sys.argv) >= 2):
        BACKUP_DIR = ""
        if ((len(sys.argv) >= 3) and (os.path.isdir(sys.argv[2]))):
            BACKUP_DIR = sys.argv[2]

        FILE_SURFIX = ""
        if (len(sys.argv) >= 4):
            FILE_SURFIX = "_"+sys.argv[3]

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
