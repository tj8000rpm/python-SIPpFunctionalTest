#!/usr/bin/python3
import os
import unittest
import inspect

from .helper import SIPpMessage, SIPp

class Test_sipp(unittest.TestCase):

    def tearDown(self):
        # delete sip message log
        if os.path.isfile(self.logfile):
            os.remove(self.logfile)
            pass

    def test_case_1_1_sip_return_code(self):
        # define a SIP message log path
        self.logfile = '{}/logs/sip_msg_{}.log'.format(os.getcwd(), inspect.currentframe().f_code.co_name)

        # run a sipp scenario
        ret, command = SIPp.helper_run_a_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
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
        ret, command = SIPp.helper_run_a_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
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
        ret, command = SIPp.helper_run_a_sipp(timeout_s=5, scenario_file='tests/scenarios/uac-uas.xml',
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
