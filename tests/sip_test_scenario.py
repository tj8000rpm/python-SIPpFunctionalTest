#!/usr/bin/python3
import os
import unittest
import inspect
from .helper import SIPpMessage, SIPp

class MyAbstractBaseTestcase(unittest.TestCase):
    ''' The class to share the tearDown process
    '''
    def tearDown(self):
        # delete sip message log
        if os.path.isfile(self.logfile):
            os.remove(self.logfile)
            pass
        # delete sipp injection file
        if os.path.isfile(self.injectionfile):
            os.remove(self.injectionfile)
            pass

class TestCase1SipBasicTest(MyAbstractBaseTestcase):

    def helper_run_sipp_test_case_1(self):
        # run a sipp scenario
        ret, command = SIPp.helper_run_a_sipp(remote_host='localhost:5062', scenario_file='tests/scenarios/uac-uas.xml',
                                              request_service='0312341234', injection_file=self.injectionfile,
                                              bind_sip_addr='127.0.0.1', bind_sip_port=5062,
                                              logfile_path=self.logfile)
        # check sipp return code
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')

    def test_case_1_1_sip_return_code(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        # define and create a SIPp injection file
        self.injectionfile = '{}/inputs/inf_{}.csv'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        SIPp.helper_write_injection_file(SIPp.helper_create_injection(content=[['user1', 'Joe']]),
                                         path_to_file=self.injectionfile)

        # run test csae 1 sipp scenario
        self.helper_run_sipp_test_case_1()

        # check sip message
        messages = SIPpMessage.messagesFilter(SIPpMessage.parseMessagesFromLogfile(self.logfile), direction='received')
        self.assertEqual(messages[-1].getStatusCode(), 200, 'Last Status code should be 200')

    def test_case_1_2_sip_header_from_between_invite_and_180(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        # define and create a SIPp injection file
        self.injectionfile = '{}/inputs/inf_{}.csv'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        SIPp.helper_write_injection_file(SIPp.helper_create_injection(content=[['user1', 'Joe']]),
                                         path_to_file=self.injectionfile)
        # run test csae 1 sipp scenario
        self.helper_run_sipp_test_case_1()

        # check sip message
        messages = SIPpMessage.parseMessagesFromLogfile(self.logfile)
        # separate message by recived and sent
        messages_r = SIPpMessage.messagesFilter(messages, direction='received')
        messages_s = SIPpMessage.messagesFilter(messages, direction='sent')

        # get first invite message and recived 180 Ringing message
        first_invite = SIPpMessage.messagesFilter(messages_s, method='INVITE')[0]
        ringing_msg = SIPpMessage.messagesFilter(messages_r, status_code=180)[0]
        # get from header values from invite and ringing message
        from_header_sent = first_invite.getHeaderValues('from')[0]
        from_header_recv = ringing_msg.getHeaderValues('from')[0]

        # compare from header's value between invite and ringing
        self.assertEqual(from_header_sent, from_header_recv, 'from header must be matched.')

    def test_case_1_3_sip_header_to_between_invite_and_180(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        # define and create a SIPp injection file
        self.injectionfile = '{}/inputs/inf_{}.csv'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        SIPp.helper_write_injection_file(SIPp.helper_create_injection(content=[['user1', 'Joe']]),
                                         path_to_file=self.injectionfile)
        # run test csae 1 sipp scenario
        self.helper_run_sipp_test_case_1()

        # check sip message
        messages = SIPpMessage.parseMessagesFromLogfile(self.logfile)
        # separate message by recived and sent
        messages_r = SIPpMessage.messagesFilter(messages, direction='received')
        messages_s = SIPpMessage.messagesFilter(messages, direction='sent')

        # get first invite message and recived 180 Ringing message
        first_invite = SIPpMessage.messagesFilter(messages_s, method='INVITE')[0]
        ringing_msg = SIPpMessage.messagesFilter(messages_r, status_code=180)[0]
        # get to header values from invite and ringing message
        to_header_sent = first_invite.getHeaderValues('to')[0]
        to_header_recv = ringing_msg.getHeaderValues('to')[0]

        # check that the to tag was added 
        self.assertNotRegex(to_header_sent, r';[\s]*tag[\s]*=[\s]*', 'to tag must be NOT included.')
        self.assertRegex(to_header_recv, r';[\s]*tag[\s]*=[\s]*', 'to tag must be included.')

class TestCase2SipErrorTest(MyAbstractBaseTestcase):

    def helper_run_sipp_test_case_2(self):
        # run a sipp scenario
        ret, command = SIPp.helper_run_a_sipp(timeout_s=5, remote_host='localhost:5062', scenario_file='tests/scenarios/uac-uas.xml',
                                              request_service='0312341234', duration_ms=int(0.5 * 1000), injection_file=self.injectionfile,
                                              bind_sip_addr='127.0.0.1', bind_sip_port=5062,
                                              logfile_path=self.logfile)
        # check sipp return code
        self.assertNotEqual(ret.returncode, 124, 'the program has time out.')
        self.assertEqual(ret.returncode, 0, 'non zero return: the program was not stop as normally.')

    def test_case_2_1_sip_return_code_in_busy(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        # define and create a SIPp injection file
        self.injectionfile = '{}/inputs/inf_{}.csv'.format(os.getcwd(), inspect.currentframe().f_code.co_name)
        SIPp.helper_write_injection_file(SIPp.helper_create_injection(content=[['user2', 'John']]),
                                         path_to_file=self.injectionfile)
        # run test csae 1 sipp scenario
        self.helper_run_sipp_test_case_2()

        # check sip message
        pass

