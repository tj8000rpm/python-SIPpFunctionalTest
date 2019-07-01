#!/usr/bin/python3
import re
import subprocess
import csv
import unittest
import uuid
import os
from datetime import datetime

class SIPp():

    @staticmethod
    def helper_run_a_sipp(**kwargs):
        timeout_s = kwargs.get('timeout_s', 10)
        remote_host = kwargs.get('remote_host', 'localhost')
        scenario_file = kwargs.get('scenario_file', None)
        request_service = kwargs.get('request_service', None)
        duration_msec = kwargs.get('duration_msec', None)
        logfile_path = kwargs.get('logfile_path', None)
        injection_file = kwargs.get('injection_file', None)
        embedded_scenario = kwargs.get('embedded_scenario', None)
        bind_sip_addr = kwargs.get('bind_sip_addr', None)
        bind_sip_port = kwargs.get('bind_sip_port', None)
        bind_media_addr = kwargs.get('bind_media_addr', None)
        bind_media_port = kwargs.get('bind_media_port', None)
        call_rate = kwargs.get('call_rate', None)
        count = kwargs.get('count', 1)

        # create sipp command line
        command = ['sipp']
        if scenario_file:
            command.append('-sf')
            command.append(str(scenario_file))
        if injection_file:
            command.append('-inf')
            command.append(str(injection_file))
        if request_service:
            command.append('-s')
            command.append(str(request_service))
        if duration_msec:
            command.append('-d')
            command.append(str(duration_msec))
        if bind_sip_addr:
            command.append('-i')
            command.append(str(bind_sip_addr))
        if bind_sip_port:
            command.append('-p')
            command.append(str(bind_sip_port))
        if bind_media_addr:
            command.append('-mi')
            command.append(str(bind_media_addr))
        if bind_media_port:
            command.append('-mp')
            command.append(str(bind_media_port))
        if logfile_path:
            command.append('-trace_msg')
            command.append('-message_file')
            command.append(str(logfile_path))
        if embedded_scenario:
            command.append('-sn')
            command.append(str(embedded_scenario))
        if call_rate:
            command.append('-r')
            command.append(str(call_rate))
        if count:
            command.append('-m')
            command.append(str(count))
        command.append(str(remote_host))

        # append in front timeout command
        runnable = ['timeout', str(timeout_s)] + command
        # execute sipp program with headless mode
        ret = subprocess.run(runnable, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # return value of subprocess results and executed command line
        return ret, " ".join(command)

    @staticmethod
    def helper_create_injection(mode="SEQUENTIAL",
                                printf=None, printfmultiple=None, printfoffset=None,
                                content=None):
        if not printf and (printfmultiple or printfoffset):
            return None

        return_str=str(mode)
        if printf:
            return_str+=',PRINTF={}'.format(str(printf))
        if printfmultiple:
            return_str+=',PRINTFMULTIPLE={}'.format(str(printfmultiple))
        if printfoffset:
            return_str+=',PRINTFOFFSET={}'.format(str(printfoffset))
        return_str+="\n"
        if content:
            for a_line in content:
                return_str+=";".join(a_line)+"\n"
        return return_str.strip()

    @staticmethod
    def helper_write_injection_file(content_as_str, path_to_file):
        with open(path_to_file, 'w') as f:
            f.write(content_as_str)

class SIPpMessage():
    message = ''
    datetime = None
    direction = None
    protocol = None
    length = 0

    def getStatusCode(self):
        status_line = self.message.split('\n')[0].strip()
        try:
            return int(status_line.split(' ')[1])
        except ValueError:
            pass
        return None

    def getStatusPhrease(self):
        status_line = self.message.split('\n')[0].strip()
        return " ".join(status_line.split(' ')[2:])

    def getMethod(self):
        request_line = self.message.split('\n')[0].strip()
        return request_line.split(' ')[0]

    def getRequstURI(self):
        request_line = self.message.split('\n')[0].strip()
        return request_line.split(' ')[1]

    def getHeaderValues(self, header_name):
        header_values=[]

        temp=[]
        renew_msg = ''
        for line in self.message.split('\n'):
            if line.strip() == '':
                break
            if line[0] == ' ' or line[0] == '\t':
                renew_msg=renew_msg.rstrip()
            renew_msg+=line.strip()+'\r\n'

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
        arrow = '<'
        if self.direction == 'sent':
            arrow = '>'
        msg += '-- {}\n'.format(self.datetime)
        for line in self.message.split('\n'):
            msg+='{} {}\n'.format(arrow, line)
        return msg

    @staticmethod
    def parseMessagesFromLogfile(filepath):
        #'----------------------------------------------- 2019-06-29 19:42:16.839845'
        re_delim_and_timestamp=re.compile(r'^-[-]+ ([\d]{4}-[\d]{2}-[\d]{2}) '
                                           '([\d]{2}:[\d]{2}:[\d]{2}\.[\d]{6}).*$')
        #'UDP message sent (442 bytes):'
        re_message_protocol=re.compile(r'^(UDP|TCP|SCTP) message (sent|received) '
                                        '[^\d]*([\d]+)[^\d]*bytes.*$')

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
                    obj.datetime = datetime.strptime('{} {}'.format(date, time), 
                                                     "%Y-%m-%d %H:%M:%S.%f")

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
        newmessages=[]
        for msg in messages:
            if direction != None and msg.direction == direction or \
               method != None and msg.getMethod() == method or \
               status_code != None and msg.getStatusCode() == status_code:
                newmessages.append(msg)
        return newmessages

class TestSIPp(unittest.TestCase):
    def test_helper_run_a_sipp_no_options(self):
        ret, command = SIPp.helper_run_a_sipp()
        self.assertRegex(command, r'^sipp')
        self.assertRegex(command, 'localhost')
        self.assertNotIn('-sf ', command)
        self.assertNotIn('-sn ', command)
        self.assertNotIn('-inf ', command)
        self.assertNotIn('-s ', command)
        self.assertNotIn('-d ', command)
        self.assertNotIn('-i ', command)
        self.assertNotIn('-p ', command)
        self.assertNotIn('-mi ', command)
        self.assertNotIn('-mp ', command)
        self.assertNotIn('-trace_msg ', command)
        self.assertNotIn('-message_file ', command)
        self.assertIn('-m 1 ', command)

    def test_helper_run_a_sipp_sf_options(self):
        ret, command = SIPp.helper_run_a_sipp(scenario_file='/dev/null')
        self.assertRegex(command, r'^sipp')
        self.assertRegex(command, 'localhost')
        self.assertIn('-sf /dev/null', command)

    def test_helper_run_a_sipp_sn_options(self):
        ret, command = SIPp.helper_run_a_sipp(embedded_scenario='hoge')
        self.assertIn('-sn hoge', command)

    def test_helper_run_a_sipp_inf_options(self):
        ret, command = SIPp.helper_run_a_sipp(injection_file='/dev/null')
        self.assertIn('-inf /dev/null', command)

    def test_helper_run_a_sipp_i_options(self):
        ret, command = SIPp.helper_run_a_sipp(bind_sip_addr='127.0.0.1')
        self.assertIn('-i 127.0.0.1 ', command)

    def test_helper_run_a_sipp_p_options(self):
        ret, command = SIPp.helper_run_a_sipp(bind_sip_port=5062)
        self.assertIn('-p 5062 ', command)

    def test_helper_run_a_sipp_mi_options(self):
        ret, command = SIPp.helper_run_a_sipp(bind_media_addr='127.0.0.1')
        self.assertIn('-mi 127.0.0.1 ', command)

    def test_helper_run_a_sipp_mp_options(self):
        ret, command = SIPp.helper_run_a_sipp(bind_media_port=60600)
        self.assertIn('-mp 60600 ', command)

    def test_helper_run_a_sipp_s_options(self):
        ret, command = SIPp.helper_run_a_sipp(request_service='service')
        self.assertIn('-s service ', command)

    def test_helper_run_a_sipp_d_options(self):
        ret, command = SIPp.helper_run_a_sipp(duration_msec=10)
        self.assertIn('-d 10', command)

    def test_helper_run_a_sipp_message_file_options(self):
        ret, command = SIPp.helper_run_a_sipp(logfile_path='/dev/null')
        self.assertIn('-trace_msg ', command)
        self.assertIn('-message_file /dev/null ', command)
        self.assertIn('-m 1 ', command)

    def test_helper_run_a_sipp_r_options(self):
        ret, command = SIPp.helper_run_a_sipp(call_rate=10)
        self.assertIn('-r 10', command)

    def test_helper_run_a_sipp_m_options(self):
        ret, command = SIPp.helper_run_a_sipp(count=20)
        self.assertIn('-m 20 ', command)

    def test_helper_run_a_sipp_timeout(self):
        ret, command = SIPp.helper_run_a_sipp(timeout_s=0.000001)
        self.assertEqual(ret.returncode, 124)

    def test_helper_create_injection_sequential(self):
        injection_content=[
            ["tst1234","example.com","192.168.0.1",
                "pass%04d","[authentication username=joe password=schmo]"],
            ["tst4321","example.com","192.168.0.2",
                "pass%04d","[authentication username=john password=smith]"]
        ]
        filecontent_str = SIPp.helper_create_injection(mode='SEQUENTIAL', content=injection_content)
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0], 'SEQUENTIAL')
        self.assertEqual(contents[1], 'tst1234;example.com;192.168.0.1;'
                'pass%04d;[authentication username=joe password=schmo]')
        self.assertEqual(contents[2], 'tst4321;example.com;192.168.0.2;'
                'pass%04d;[authentication username=john password=smith]')

    def test_helper_create_injection_random(self):
        filecontent_str = SIPp.helper_create_injection(mode='RANDOM')
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'RANDOM')

    def test_helper_create_injection_users(self):
        filecontent_str = SIPp.helper_create_injection(mode='USERS')
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'USERS')

    def test_helper_create_injection_printf(self):
        filecontent_str = SIPp.helper_create_injection(mode='USERS', printf=4)
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'USERS,PRINTF=4')

    def test_helper_create_injection_printfmultiple(self):
        filecontent_str = SIPp.helper_create_injection(mode='USERS', printf=4, printfmultiple=2)
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'USERS,PRINTF=4,PRINTFMULTIPLE=2')

    def test_helper_create_injection_printfoffset(self):
        filecontent_str = SIPp.helper_create_injection(mode='USERS', printf=4, printfoffset=10)
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'USERS,PRINTF=4,PRINTFOFFSET=10')

    def test_helper_create_injection_printfmultipleoffset(self):
        filecontent_str = SIPp.helper_create_injection(mode='USERS', 
                                                       printf=4, printfmultiple=2, printfoffset=10)
        contents = filecontent_str.split('\n')
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0], 'USERS,PRINTF=4,PRINTFMULTIPLE=2,PRINTFOFFSET=10')

    def test_helper_create_injection_multiple(self):
        filecontent_str = SIPp.helper_create_injection(mode='SEQUENTIAL', printfmultiple=10)
        self.assertEqual(None, filecontent_str)

    def test_helper_create_injection_offset(self):
        filecontent_str = SIPp.helper_create_injection(mode='sequential', printfoffset=10)
        self.assertEqual(None, filecontent_str)

    def test_helper_create_injection_multipleoffset(self):
        filecontent_str = SIPp.helper_create_injection(mode='SEQUENTIAL', 
                                                       printfmultiple=10, printfoffset=10)
        self.assertEqual(None, filecontent_str)

    def test_helper_write_injection_file(self):
        content_as_str = 'ACCCDCCCVDYHJKOIHJJKJLK!@#$%12346'
        path_to_file = './inputs/{}'.format(str(uuid.uuid4()))
        try:
            SIPp.helper_write_injection_file(content_as_str=content_as_str,
                                             path_to_file=path_to_file)
            self.assertEqual(os.path.isfile(path_to_file), True)
            with open(path_to_file) as f:
                content = f.read()
            self.assertEqual(content, 'ACCCDCCCVDYHJKOIHJJKJLK!@#$%12346')
        finally:
            if os.path.isfile(path_to_file):
                os.remove(path_to_file)

class TestSIPpMessage(unittest.TestCase):
    def createNewMsg(self):
        msg = SIPpMessage()
        msg.datetime = datetime.now()
        msg.protocol = 'UDP'
        msg.direction = 'received'
        return msg

    def setUp(self):
        self.msg = self.createNewMsg()

    def setRequestMessage(self, msg):
        msg.message = ( 'INVITE sip:bob@biloxi.com SIP/2.0\r\n'
                         'Via: SIP/2.0/UDP pc33.atlanta.com;branch=z9hG4bKnashds8\r\n'
                         'To: Bob <bob@biloxi.com>\r\n'
                         'From: Alice <alice@atlanta.com>;tag=1928301774\r\n'
                         'Call-ID: a84b4c76e66710\r\n'
                         'CSeq: 314159 INVITE\r\n'
                         'Max-Forwards: 70\r\n'
                         'Date: Thu, 21 Feb 2002 13:02:03 GMT\r\n'
                         'Contact: <sip:alice@pc33.atlanta.com>\r\n'
                         'Content-Type: application/sdp\r\n'
                         'Content-Length: 147\r\n'
                         '\r\n'
                         'v=0\r\n'
                         'o=UserA 2890844526 2890844526 IN IP4 here.com\r\n'
                         's=Session SDP\r\n'
                         'c=IN IP4 pc33.atlanta.com\r\n'
                         't=0 0\r\n'
                         'm=audio 49172 RTP/AVP 0\r\n'
                         'a=rtpmap:0 PCMU/8000')
        msg.length = len(self.msg.message.encode('utf-8'))


    def setResponseMessage(self, msg):
        msg.message = ( 'SIP/2.0 181 Call Is Being Forwarded\r\n'
                        'Via: SIP/2.0/UDP server10.biloxi.com;branch=z9hG4bK4b43c2ff8.1\r\n'
                        ' ;received=192.0.2.3\r\n'
                        'Via: SIP/2.0/UDP bigbox3.site3.atlanta.com;' # this line is not broken
                                                         'branch=z9hG4bK77ef4c2312983.1\r\n'
                        ' ;received=192.0.2.2\r\n'
                        'Via: SIP/2.0/UDP pc33.atlanta.com;branch=z9hG4bKnashds8\r\n'
                        ' ;received=192.0.2.1\r\n'
                        'To: Bob <sip:bob@biloxi.com>;tag=a6c85cf\r\n'
                        'From: Alice <sip:alice@atlanta.com>;tag=1928301774\r\n'
                        'Call-ID: a84b4c76e66710\r\n'
                        'Contact: <sip:bob@192.0.2.4>\r\n'
                        'CSeq: 314159 INVITE\r\n'
                        'Content-Length: 0\r\n'
                        '\r\n')
        msg.length = len(self.msg.message.encode('utf-8'))

    def test_getStatusCode(self):
        self.setResponseMessage(self.msg)
        self.assertEqual(181, self.msg.getStatusCode())

    def test_getStatusCodeInRequest(self):
        self.setRequestMessage(self.msg)
        self.assertEqual(None, self.msg.getStatusCode())

    def test_getStatusPhrease(self):
        self.setResponseMessage(self.msg)
        self.assertEqual('Call Is Being Forwarded', self.msg.getStatusPhrease())

    def test_getStatusPhreaseInRequest(self):
        self.setRequestMessage(self.msg)
        self.assertEqual('SIP/2.0', self.msg.getStatusPhrease())

    def test_getMethod(self):
        self.setRequestMessage(self.msg)
        self.assertEqual('INVITE', self.msg.getMethod())

    def test_getMethodInResonse(self):
        self.setResponseMessage(self.msg)
        self.assertEqual('SIP/2.0', self.msg.getMethod())

    def test_getRequstURI(self):
        self.setRequestMessage(self.msg)
        self.assertEqual('sip:bob@biloxi.com', self.msg.getRequstURI())

    def test_getRequstURIInResponse(self):
        self.setResponseMessage(self.msg)
        self.assertEqual('181', self.msg.getRequstURI())

    def test_getHeaderValues(self):
        self.setResponseMessage(self.msg)
        self.assertEqual('Bob <sip:bob@biloxi.com>;tag=a6c85cf', self.msg.getHeaderValues('To')[0])
        self.assertEqual('Bob <sip:bob@biloxi.com>;tag=a6c85cf', self.msg.getHeaderValues('to')[0])
        self.assertEqual('Bob <sip:bob@biloxi.com>;tag=a6c85cf', self.msg.getHeaderValues('tO')[0])
        self.assertEqual('SIP/2.0/UDP server10.biloxi.com;'
                         'branch=z9hG4bK4b43c2ff8.1;received=192.0.2.3',
                         self.msg.getHeaderValues('Via')[0])
        self.assertEqual('SIP/2.0/UDP pc33.atlanta.com;'
                         'branch=z9hG4bKnashds8;received=192.0.2.1',
                         self.msg.getHeaderValues('Via')[2])

    def test_messagesFilter(self):
        msg1 = self.createNewMsg()
        msg1.direction = 'sent'
        self.setRequestMessage(msg1)

        msg2 = self.createNewMsg()
        msg2.direction = 'received'
        self.setResponseMessage(msg2)

        msg3 = self.createNewMsg()
        msg3.direction = 'received'
        self.setResponseMessage(msg3)

        messages = [msg1, msg2, msg3]

        new_messages = SIPpMessage.messagesFilter(messages, method='INVITE')
        self.assertEqual(len(new_messages), 1)
        self.assertEqual(new_messages[0].getMethod(), 'INVITE')

        new_messages = SIPpMessage.messagesFilter(messages, method='BYE')
        self.assertEqual(len(new_messages), 0)

        new_messages = SIPpMessage.messagesFilter(messages, direction='sent')
        self.assertEqual(len(new_messages), 1)
        self.assertEqual(new_messages[0].getMethod(), 'INVITE')

        new_messages = SIPpMessage.messagesFilter(messages, direction='received')
        self.assertEqual(len(new_messages), 2)
        self.assertEqual(new_messages[0].getStatusCode(), 181)
        self.assertEqual(new_messages[1].getStatusCode(), 181)

        new_messages = SIPpMessage.messagesFilter(messages, status_code=181)
        self.assertEqual(len(new_messages), 2)
        self.assertEqual(new_messages[0].getStatusCode(), 181)
        self.assertEqual(new_messages[1].getStatusCode(), 181)

        new_messages = SIPpMessage.messagesFilter(messages, status_code=180)
        self.assertEqual(len(new_messages), 0)

    def test_as_str(self):
        self.setRequestMessage(self.msg)
        dump = str(self.msg)

        for line in dump.strip().split('\n')[1:]:
            self.assertEqual(line[0], '<')
