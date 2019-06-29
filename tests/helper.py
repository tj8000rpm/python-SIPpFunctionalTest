#!/usr/bin/python3
import re
import subprocess
from datetime import datetime

class SIPp():

    @staticmethod
    def helper_run_a_sipp(timeout_s, scenario_file, request_service, duration_ms, logfile_path):
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

