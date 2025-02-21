import requests
import codecs

from bs4 import BeautifulSoup
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


def log_in(luxmed_login: str, luxmed_password: str) -> requests.Session:
    """
    Log in to Luxmed's patient portal.

    :param luxmed_login: Luxmed account login (usually an email address).
    :param luxmed_password: Luxmed account password.
    :return: Session object if login is successful, None otherwise.
    """
    login_page_url = 'https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/Page/Account/Login'
    authentication_url = 'https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogIn'

    with requests.Session() as session:
        response = session.get(login_page_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        csrf_token_element = soup.find('input', {'name': '__RequestVerificationToken'})
        csrf_token = csrf_token_element['value'] if csrf_token_element else None

        if csrf_token is None:
            print('CSRF token not found.')
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'pl,en;q=0.7,en-US;q=0.3',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://portalpacjenta.luxmed.pl',
            'Referer': login_page_url,
            'X-Requested-With': 'XMLHttpRequest'
        }

        login_payload = {
            'Login': luxmed_login,
            'Password': luxmed_password,
            '__RequestVerificationToken': csrf_token
        }

        response = session.post(authentication_url, json=login_payload, headers=headers)

        try:
            response_json = response.json()
        except ValueError:
            print('Failed to parse JSON response. Response content:', response.text)
            return None

        if response_json.get('succeded') and response_json.get('token'):
            print('Login successful.')
            return session

        print('Login failed:', response_json.get('errorMessage'))
        return None


def log_out(session: requests.Session):
    """
    Log out from Luxmed's patient portal using a session context.
    :return: None
    """
    session.get('https://portalpacjenta.luxmed.pl/PatientPortal/Account/LogOut')


def find(session, service_id, date_from, date_to, doctor_id='0', city_id='1', clinic_id='', time_option='Any'):
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

    find_page_url = 'https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/Page/Reservation/Results'

    date_from = '2025-02-21'
    date_to = '2025-03-06'

    search_params = {
        'cityId': city_id,
        'doctorIds': [],
        'facilityIds': [],
        'languageId': 10,
        'partsOfDay': {0: '0'},
        'referralTypeId': None,
        'searchDateFrom': date_from,
        'searchDateTo': date_to,
        'serviceVariantId': 4468,
    }

    print(search_params)

    r = session.post(find_page_url, json=search_params)
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
    soup = BeautifulSoup(html_page, 'html.parser')
    if 'nie ma dostępnych terminów' in soup.text:
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
    # parser.add_argument('email', help='email address')
    parser.add_argument('datefrom', help='Date format dd-mm-yyyy')
    parser.add_argument('dateto', help='Date format dd-mm-yyyy')
    parser.add_argument('serviceid', help='Type of specialist. ID should be taken from csv in repository.')
    # parser.add_argument('doctorid', help='Doctor id. ID should be take from csv in repository.')
    # parser.add_argument('cityid', help='City id. ID should be taken from csv in repository.')
    # parser.add_argument('clinicid', help='Clinic id. ID should be taken from csv in repository.')
    # parser.add_argument('timeoption', help='Time option from range: Morning, Afternoon, Evening or Any')
    args = parser.parse_args()

    session = log_in(args.lxlogin, args.lxpass)
    isav = find(session, service_id=args.serviceid, date_from=args.datefrom, date_to=args.dateto)
    # if isav:
    #    notify('Wizyta znaleziona dla uzytkownika: %s' % args.lxlogin, args.email)
    log_out(session)


if __name__ == '__main__':
    main()
