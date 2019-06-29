#!/usr/bin/python3
import re
import os
import subprocess
import unittest
import inspect
from datetime import datetime

class SIPpMessage():
    message = ''
    datetime = None
    direction = None
    protocol = None
    length = 0

    def getStatusCode(self):
        status_line = self.message.split('\n')[0]
        try:
            return int(status_line.split(' ')[1])
        except ValueError:
            pass
        return None

    def getStatusPhrease(self):
        status_line = self.message.split('\n')[0]
        return " ".join(status_line.split(' ')[2:])

    def getMethod(self):
        request_line = self.message.split('\n')[0]
        return request_line.split(' ')[0]

    def getRequstURI(self):
        request_line = self.message.split('\n')[0]
        return request_line.split(' ')[1]

    def getHeader(self, header_name):
        header_values=[]
        renew_msg = ''
        for line in self.message.split('\n'):
            if line.strip() == '':
                break
            renew_msg += line.strip()
            if line[0] == ' ' or line[0] == '\t':
                continue
            renew_msg += '\n'

        renew_msg = renew_msg.strip()

        for line in renew_msg.split('\n'):
            kv = line.split(':', 1)
            kv.append('')

            key = kv[0].strip().lower()
            value = kv[1].strip()

            if header_name.lower() == key:
                header_values.append(value)

        return header_values

    def __str__(self):
        msg=''
        allow = '<'
        if self.direction == 'sent':
            allow = '>'
        msg += '-- {}\n'.format(self.datetime)
        for line in self.message.split('\n'):
            msg+='{} {}\n'.format(allow, line)

        return msg

    @staticmethod
    def parseMessagesFromLogfile(filepath):
        #'----------------------------------------------- 2019-06-29 19:42:16.839845'
        re_delim_and_timestamp=re.compile(r'^-[-]+ ([\d]{4}-[\d]{2}-[\d]{2}) ([\d]{2}:[\d]{2}:[\d]{2}\.[\d]{6}).*$')
        #'UDP message sent (442 bytes):'
        re_message_protocol=re.compile(r'^(UDP|TCP|SCTP) message (sent|received) [^\d]*([\d]+)[^\d]*bytes.*$')

        messages = []
        pointer=None
        # check sip messages
        with open(filepath, 'r') as f:
            for line in f.read().split('\n'):
                match_deli = re_delim_and_timestamp.match(line)
                match_prot = re_message_protocol.match(line)

                if match_deli:
                    date = match_deli.group(1)
                    time = match_deli.group(2)
                    obj = SIPpMessage()
                    obj.datetime = datetime.strptime('{} {}'.format(date, time), "%Y-%m-%d %H:%M:%S.%f")

                    messages.append(obj)
                    pointer=messages[-1]

                elif match_prot:
                    pointer.protocol = match_prot.group(1)
                    pointer.direction = match_prot.group(2)
                    pointer.length = int(match_prot.group(3))

                else:
                    pointer.message += line+'\n'
                    pointer.message = pointer.message.lstrip()


        for msg in messages:
            msg.message = ((msg.message.lstrip().encode('utf-8'))[:msg.length]).decode('utf-8')

        return messages

    @staticmethod
    def messagesFilter(messages, direction=None, method=None, status_code=None):
        for msg in messages:
            if direction != None and msg.direction == direction or \
               method != None and msg.getMethod() == method or \
               status_code != None and msg.getStatusCode() == status_code:
                newmessages.append(msg)
        return newmessages

    @staticmethod
    def filterByDirection(messages, direction):
        newmessages=[]
        for msg in messages:
            if msg.direction == direction:
                newmessages.append(msg)
        return newmessages

    @staticmethod
    def filterByMethod(messages, method):
        newmessages=[]
        for msg in messages:
            if msg.getMethod() == method:
                newmessages.append(msg)
        return newmessages

    @staticmethod
    def filterByStatusCode(messages, status_code):
        newmessages=[]
        for msg in messages:
            if msg.getStatusCode() == status_code:
                newmessages.append(msg)
        return newmessages

class Test_sipp(unittest.TestCase):

    def helper_run_sipp(self, timeout_s, scenario_file, request_service, duration_ms, logfile_path):
        # create sipp command line
        command = ('sipp '
                   '-m 1 '
                   '-sf {} '
                   '-s {} '
                   '-d {} '
                   '-trace_msg '
                   '-message_file {} '
                   'localhost').format(scenario_file, request_service, duration_ms, logfile_path)
        # append in front timeout command
        runnable = ['timeout', str(timeout_s)] + command.split(' ')

        # execute sipp program
        ret = subprocess.run(runnable, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ret, command

    def tearDown(self):
        # delete sip message log
        if os.path.isfile(self.logfile):
            os.remove(self.logfile)
            pass

    def test_case_1_1_sip_return_code(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)

        # run a sipp scenario
        ret, command = self.helper_run_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
                                       request_service='0312341234', duration_ms=int(0.5 * 1000),
                                       logfile_path=self.logfile)

        # check sipp return code
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')

        # check sip message
        messages = SIPpMessage.filterByDirection(SIPpMessage.parseMessagesFromLogfile(self.logfile), 'received')
        self.assertEqual(messages[-1].getStatusCode(), 200, 'Last Status code should be 200')

    def test_case_1_2_sip_header_from_between_invite_and_180(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)

        # run a sipp scenario
        ret, command = self.helper_run_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
                                       request_service='0312341234', duration_ms=int(0.5 * 1000),
                                       logfile_path=self.logfile)

        # check sipp return code
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')

        # check sip message
        messages = SIPpMessage.parseMessagesFromLogfile(self.logfile)
        messages_r = SIPpMessage.filterByDirection(messages, 'received')
        messages_s = SIPpMessage.filterByDirection(messages, 'sent')
        first_invite = SIPpMessage.filterByMethod(messages_s, 'INVITE')[0]
        ringing_msg = SIPpMessage.filterByStatusCode(messages_r, 180)[0]
        from_header_sent = first_invite.getHeader('from')[0]
        from_header_recv = ringing_msg.getHeader('from')[0]
        self.assertEqual(from_header_sent, from_header_recv, 'from header must be matched.')

    def test_case_1_3_sip_header_to_between_invite_and_180(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)

        # run a sipp scenario
        ret, command = self.helper_run_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
                                       request_service='0312341234', duration_ms=int(0.5 * 1000),
                                       logfile_path=self.logfile)

        # check sipp return code
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')

        # check sip message
        messages = SIPpMessage.parseMessagesFromLogfile(self.logfile)
        messages_r = SIPpMessage.filterByDirection(messages, 'received')
        messages_s = SIPpMessage.filterByDirection(messages, 'sent')
        first_invite = SIPpMessage.filterByMethod(messages_s, 'INVITE')[0]
        ringing_msg = SIPpMessage.filterByStatusCode(messages_r, 180)[0]
        to_header_sent = first_invite.getHeader('to')[0]
        to_header_recv = ringing_msg.getHeader('to')[0]
        self.assertNotIn('tag=', to_header_sent, 'to tag must be NOT included.')
        self.assertIn('tag=', to_header_recv, 'to tag must be included.')
