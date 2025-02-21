import requests
import codecs
from lxml import etree
import smtplib
import string
import argparse
import getpass


def notify(email_text, dst_email):
    """
    Function sends emails.
    :param email_text:
    :param dst_email:
    :return:
    """
    smtpobj = smtplib.SMTP_SSL('poczta.o2.pl', 465)

    smtpobj.ehlo()
    smtpobj.login('abusemenot@tlen.pl', 'ABUSEMENOTLUXMED')

    from_ = 'powiadomienie@o-wizycie.pl',
    to_ = dst_email
    subject_ = 'Szukana wizyta jest dostepna w placowce Luxmed'
    text_ = email_text
    body_ = string.join(("From: %s" % from_, "To: %s" % to_, "Subject: %s" % subject_, "", text_), "\r\n")
    smtpobj.sendmail('abusemenot@tlen.pl', [to_], body_)
    smtpobj.quit()


def write_to_file(text, file_path='log.txt'):
    """
    Write To File
    :param text: text which will be written to file
    :param file_path: file path
    :return:
    """
    with codecs.open(file_path, 'a', 'utf-8') as f:
        f.write(text)


def log_in(login, password):
    """
    Login to Luxmed's patient portal
    :param login: Luxmed account login. Usually e-mail address.
    :param password: You know...
    :return: Session object.
    """
    log_in_params = {'Login': login, 'Password': password}
    s = requests.Session()
    s.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0'})
    s.headers.update({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    s.headers.update({'Referer': 'https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogOn'})
    s.cookies.update({'LXCookieMonit': '1'})
    r = s.post('https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogIn', data=log_in_params)

    if 'Zarezerwuj' in r.text:
        print('Login succeed')
        return s
    else:
        print('Login failed')
        return None


def log_out(session):
    """
    Log out from Luxmed's patient portal
    :param session: Session object
    :return
    """
    r = session.get('https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogOut')
    if 'bezpiecznie wylogowany' in r.text:
        print('Logout succeed')
    else:
        print('Logout failed')


def find(session, service_id, date_from, date_to, doctor_id='0', city_id='5', clinic_id='', time_option='Any'):
    """
    Find appointment.
    :param session: session object is created during log in and passed to the function
    :param service_id: type of service example: orthopaedist, general practitioner
    :param date_from: date range start
    :param date_to: date range end
    :param doctor_id: not all of them are worth your health ;)
    :param city_id: default is Warsaw
    :param clinic_id: nearest is the best
    :param time_option: Morning, Afternoon, Evening or Any
    :return:
    """

    main_page_url = 'https://portalpacjenta.luxmed.pl/PatientPortal/'
    find_page_url = 'https://portalpacjenta.luxmed.pl/PatientPortal/Reservations/Reservation/Find'

    search_params = {
        'DateOption': 'SelectedDate',
        'CityId': city_id,
        'ClinicId': clinic_id,
        'ServiceId': service_id,
        'DoctorMultiIdentyfier': "%s-%s-%s" % (doctor_id, service_id, clinic_id),
        'PayedOption': 'Free',
        'SearchFirstFree': 'false',
        'DateFrom': date_from,
        'DateTo': date_to,
        'TimeOption': time_option}

    print(search_params)

    r = session.get(main_page_url)

    parser = etree.HTMLParser()
    tree = etree.fromstring(r.text, parser)

    verification_token = tree.xpath('//form//input[@name="__RequestVerificationToken"]/@value')
    search_params['__RequestVerificationToken'] = verification_token[0]

    r = session.post(find_page_url, data=search_params)
    # wtf(r.text)

    if is_appointment_available(r.text):
        print('Hurray! Visit has been found :)')
        return True
    else:
        print('Pity :( Visit has not been found.')
        return False


def is_appointment_available(html_page):
    """
    Let's see if you found your appointment.
    :param html_page: web page source
    :return: True if you are lucky
    """
    if 'Brak dostępnych terminów w dniach'.decode('utf-8') in unicode(html_page):
        return False
    if 'Niestety, nie dysponujemy terminami wizyt we wskazanym zakresie w rezerwacji'.decode('utf-8') in html_page:
        return False
    else:
        return True


def parse_results(html_page):
    pass


def book_appointment():
    pass


def main():
    """
    Main function where everything happens.
    1. Login to the website
    2. Check if queried appointment is available
    3. Do something with it
    4. Logout
    :return:
    """
    parser = argparse.ArgumentParser(description='Luxmed appointment availability checker.')
    parser.add_argument('lxlogin', help='Luxmend account login')
    parser.add_argument('lxpass', help='Luxmed account password')
    parser.add_argument('email', help='email address')
    parser.add_argument('datefrom', help='Date format dd-mm-yyyy')
    parser.add_argument('dateto', help='Date format dd-mm-yyyy')
    parser.add_argument('serviceid', help='Type of specialist. ID should be taken from csv in repository.')
    parser.add_argument('doctorid', help='Doctor id. ID should be take from csv in repository.')
    parser.add_argument('cityid', help='City id. ID should be taken from csv in repository.')
    parser.add_argument('clinicid', help='Clinic id. ID should be taken from csv in repository.')
    parser.add_argument('timeoption', help='Time option from range: Morning, Afternoon, Evening or Any')
    args = parser.parse_args()

    session = log_in(args.lxlogin, args.lxpass)
    isav = find(session, service_id=args.serviceid, date_from=args.datefrom, date_to=args.dateto, doctor_id=args.doctorid, city_id=args.cityid, clinic_id=args.clinicid, time_option=args.timeoption)
    if isav:
        notify('Wizyta znaleziona dla uzytkownika: %s' % args.lxlogin, args.email)
    log_out(session)


if __name__ == '__main__':
    main()
