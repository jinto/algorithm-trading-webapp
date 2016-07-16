# -*- coding: utf-8 -*-
import sys
import atexit
import json
import threading
import queue

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtWidgets import QApplication


class Kiwoom():
    def __init__(self, k_queue):
        super().__init__()
        self.q = k_queue
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnReceiveTrData[str, str, str, str, str, int, str, str, str].connect(self._OnReceiveTrData)
        self.ocx.OnReceiveRealData[str, str, str].connect(self._OnReceiveRealData)
        self.ocx.OnReceiveMsg[str, str, str, str].connect(self._OnReceiveMsg)
        self.ocx.OnReceiveChejanData[str, int, str].connect(self._OnReceiveChejanData)
        self.ocx.OnEventConnect[int].connect(self._OnEventConnect)
        self.ocx.OnReceiveRealCondition[str, str, str, str].connect(self._OnReceiveRealCondition)
        self.ocx.OnReceiveTrCondition[str, str, str, int, int].connect(self._OnReceiveTrCondition)
        self.ocx.OnReceiveConditionVer[int, str].connect(self._OnReceiveConditionVer)

        atexit.register(self.quit)

    ####################################################
    # Interface Methods
    ####################################################
    def comm_connect(self):
        """
        로그인 윈도우를 실행한다.
        로그인이 성공하거나 실패하는 경우 OnEventConnect 이벤트가 발생하고 이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.

        :return: 0 - 성공, 음수값은 실패
        """
        return self.ocx.dynamicCall("CommConnect()")

    def comm_rq_data(self, sRQName, sTrCode, nPrevNext, sScreenNo):
        """
        Tran을 서버로 송신한다.

        :param sRQName: 사용자구분 명
        :param sTrCode: Tran명 입력
        :param nPrevNext: 0:조회, 2:연속
        :param sScreenNo: 4자리의 화면번호
        Ex) openApi.CommRqData( “RQ_1”, “OPT00001”, 0, “0101”);
        :return:
        OP_ERR_SISE_OVERFLOW – 과도한 시세조회로 인한 통신불가
        OP_ERR_RQ_STRUCT_FAIL – 입력 구조체 생성 실패
        OP_ERR_RQ_STRING_FAIL – 요청전문 작성 실패
        OP_ERR_NONE(0) – 정상처리
        """
        return self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", sRQName, sTrCode, nPrevNext, sScreenNo)

    def get_login_info(self, sTag):
        """
        로그인한 사용자 정보를 반환한다.

        :param sTag: 사용자 정보 구분 TAG값
            “ACCOUNT_CNT” – 전체 계좌 개수를 반환한다.
            "ACCNO" – 전체 계좌를 반환한다. 계좌별 구분은 ‘;’이다.
            “USER_ID” - 사용자 ID를 반환한다.
            “USER_NAME” – 사용자명을 반환한다.
            “KEY_BSECGB” – 키보드보안 해지여부. 0:정상, 1:해지
            “FIREW_SECGB” – 방화벽 설정 여부. 0:미설정, 1:설정, 2:해지
            Ex) openApi.GetLoginInfo(“ACCOUNT_CNT”);
        :return: TAG값에 따른 데이터 반환
        """
        return self.ocx.dynamicCall("GetLoginInfo(QString)", [sTag])

    def send_order(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        """
        주식 주문을 서버로 전송한다.

        :param sRQName: 사용자 구분 요청 명
        :param sScreenNo: 화면번호[4]
        :param sAccNo: 계좌번호[10]
        :param nOrderType: 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매 도정정)
        :param sCode: 주식종목코드
        :param nQty: 주문수량
        :param nPrice: 주문단가
        :param sHogaGb: 거래구분
            00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가, 10: 지정가IOC, 13:시장가IOC,
            16:최유리IOC, 20:지정가FOK, 23:시장가FOK, 26:최유리FOK, 61: 장전시간외종가, 62:시간외단일가, 81:장후시간외종가
            ※ 시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시간외, 장후시간외 주문시 주문가격을 입력하지 않습니다.
            ex)
            지정가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 48500, “00”, “”);
            시장가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 0, “03”, “”);
            매수 정정 - openApi.SendOrder(“RQ_1”,“0101”, “5015123410”, 5, “000660”, 10, 49500, “00”, “1”);
            매수 취소 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 3, “000660”, 10, 0, “00”, “2”);
        :param sOrgOrderNo: 원주문번호
        :return: 에러코드 - parse_error_code
        """
        return self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                    [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo])

    def send_order_credit(self):
        pass

    def set_input_value(self, sID, sValue):
        """
        Tran 입력 값을 서버통신 전에 입력한다.

        :param sID: 아이템명
        :param sValue: 입력 값
        Ex) openApi.SetInputValue(“종목코드”, “000660”);
            openApi.SetInputValue(“계좌번호”, “5015123401”);
        """
        self.ocx.dynamicCall("SetInputValue(QString, QString)", sID, sValue)

    def set_output_fid(self):
        pass

    def comm_get_data(self, sJongmokCode, sRealType, sFieldName, nIndex, sInnerFieldName):
        """
        Tran 데이터, 실시간 데이터, 체결잔고 데이터를 반환한다.

        1. Tran 데이터
        :param sJongmokCode: Tran명
        :param sRealType: 사용안함
        :param sFieldName: 레코드명
        :param nIndex: 반복인덱스
        :param sInnerFieldName: 아이템명

        2. 실시간 데이터
        :param sJongmokCode: Key Code
        :param sRealType: Real Type
        :param sFieldName: Item Index (FID)
        :param nIndex: 사용안함
        :param sInnerFieldName: 사용안함

        3. 체결 데이터
        :param sJongmokCode: 체결구분
        :param sRealType: “-1”
        :param sFieldName: 사용안함
        :param nIndex: ItemIndex
        :param sInnerFieldName: 사용안함

        :return: 요청 데이터
        """
        return self.ocx.dynamicCall("CommGetData(QString, QString, QString, int, QString)", sJongmokCode, sRealType,
                                    sFieldName, nIndex, sInnerFieldName)

    def disconnect_real_data(self, sScnNo):
        """
        화면 내 모든 리얼데이터 요청을 제거한다.
        화면을 종료할 때 반드시 위 함수를 호출해야 한다.

        :param sScnNo: 화면번호[4]
        Ex) openApi.DisconnectRealData(“0101”);
        """
        self.ocx.dynamicCall("DisconnectRealData(QString)", sScnNo)

    # 수신 받은 데이터의 반복 개수를 반환한다.
    def get_repeat_cnt(self, trCode, recordName):
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, recordName)

    # 복수종목조회 Tran을 서버로 송신한다.
    # OP_ERR_RQ_STRING – 요청 전문 작성 실패
    # OP_ERR_NONE - 정상처리
    #
    # sArrCode – 종목간 구분은 ‘;’이다.
    # nTypeFlag – 0:주식관심종목정보, 3:선물옵션관심종목정보
    def comm_kw_rq_data(self, arrCode, next, codeCount, typeFlag, sRQName, sScreenNo):
        self.ocx.dynamicCall("CommKwRqData(QString, QBoolean, int, int, QString, QString)", arrCode, next, codeCount,
                             typeFlag, sRQName, sScreenNo)

    def get_api_module_path(self):
        pass

    def get_code_list_by_market(self):
        pass

    # 로그인 상태 확인
    # 0:미연결, 1:연결완료, 그외는 에러
    def get_connect_state(self):
        return self.ocx.dynamicCall("GetConnectState()")

    # 종목코드의 한글명을 반환한다.
    # strCode – 종목코드
    # 종목한글명
    def get_master_code_name(self, code):
        return self.ocx.dynamicCall("GetMasterCodeName(QString)", code)

    def get_master_listed_stock_cnt(self):
        pass

    def get_master_construction(self):
        pass

    def get_master_listed_stock_date(self):
        pass

    def get_master_last_price(self):
        pass

    def get_master_stock_state(self):
        pass

    def get_data_count(self):
        pass

    def get_output_value(self):
        pass

    def get_comm_data(self):
        pass

    # strRealType – 실시간 구분
    # nFid – 실시간 아이템
    # Ex) 현재가출력 - openApi.GetCommRealData(“주식시세”, 10);
    # 참고)실시간 현재가는 주식시세, 주식체결 등 다른 실시간타입(RealType)으로도 수신가능
    def get_comm_real_data(self, realType, fid):
        return self.ocx.dynamicCall("GetCommRealData(QString, int)", realType, fid).strip()

    # 체결잔고 데이터를 반환한다.
    def get_chejan_data(self, fid):
        return self.ocx.dynamicCall("GetChejanData(int)", fid)

    # 실시간 등록을 한다.
    # strScreenNo : 화면번호
    # strCodeList : 종목코드리스트(ex: 039490;005930;…)
    # strFidList : FID번호(ex:9001;10;13;…)
    # 	9001 – 종목코드
    # 	10 - 현재가
    # 	13 - 누적거래량
    # strOptType : 타입(“0”, “1”)
    # 타입 “0”은 항상 마지막에 등록한 종목들만 실시간등록이 됩니다.
    # 타입 “1”은 이전에 실시간 등록한 종목들과 함께 실시간을 받고 싶은 종목을 추가로 등록할 때 사용합니다.
    # ※ 종목, FID는 각각 한번에 실시간 등록 할 수 있는 개수는 100개 입니다.
    def set_real_reg(self, sScreenNo, codeList, fidList, optType):
        return self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", sScreenNo, codeList, fidList,
                                    optType)

    # 종목별 실시간 해제
    # strScrNo : 화면번호
    # strDelCode : 실시간 해제할 종목코드
    # -화면별 실시간해제
    # 여러 화면번호로 걸린 실시간을 해제하려면 파라메터의 화면번호와 종목코드에 “ALL”로 입력하여 호출하시면 됩니다.
    # SetRealRemove(“ALL”, “ALL”);
    # 개별화면별로 실시간 해제 하시려면 파라메터에서 화면번호는 실시간해제할
    # 화면번호와 종목코드에는 “ALL”로 해주시면 됩니다.
    # SetRealRemove(“0001”, “ALL”);
    # -화면의 종목별 실시간해제
    # 화면의 종목별로 실시간 해제하려면 파라메터에 해당화면번호와 해제할
    # 종목코드를 입력하시면 됩니다.
    # SetRealRemove(“0001”, “039490”);
    def set_real_remove(self, scrNo, delCode):
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", scrNo, delCode)

    # 서버에 저장된 사용자 조건식을 가져온다.
    def get_condition_load(self):
        return self.ocx.dynamicCall("GetConditionLoad()")

    # 조건검색 조건명 리스트를 받아온다.
    # 조건명 리스트(인덱스^조건명)
    # 조건명 리스트를 구분(“;”)하여 받아온다
    def get_condition_name_list(self):
        return self.ocx.dynamicCall("GetConditionNameList()")

    # 조건검색 종목조회TR송신한다.
    # LPCTSTR strScrNo : 화면번호
    # LPCTSTR strConditionName : 조건명
    # int nIndex : 조건명인덱스
    # int nSearch : 조회구분(0:일반조회, 1:실시간조회, 2:연속조회)
    # 1:실시간조회의 화면 개수의 최대는 10개
    def send_condition(self, scrNo, conditionName, index, search):
        self.ocx.dynamicCall("SendCondition(QString,QString, int, int)", scrNo, conditionName, index, search)

    # 실시간 조건검색을 중지합니다.
    # ※ 화면당 실시간 조건검색은 최대 10개로 제한되어 있어서 더 이상 실시간 조건검색을 원하지 않는 조건은 중지해야만 카운트 되지 않습니다.
    def send_condition_stop(self, scrNo, conditionName, index):
        self.ocx.dynamicCall("SendConditionStop(QString, QString, int)", scrNo, conditionName, index)

    # 차트 조회한 데이터 전부를 배열로 받아온다.
    # LPCTSTR strTrCode : 조회한TR코드
    # LPCTSTR strRecordName: 조회한 TR명
    # ※항목의 위치는 KOA Studio의 TR목록 순서로 데이터를 가져옵니다.
    # 예로 OPT10080을 살펴보면 OUTPUT의 멀티데이터의 항목처럼 현재가, 거래량, 체결시간등 순으로 항목의 위치가 0부터 1씩 증가합니다.
    def get_comm_data_ex(self, trCode, recordName):
        return json.dumps(self.ocx.dynamicCall("GetCommDataEx(QString, QString)", trCode, recordName))

    ####################################################
    # Control Event Handlers
    ####################################################

    # Tran 수신시 이벤트
    def _OnReceiveTrData(self, scrNo, sRQName, trCode, recordName, prevNext, dataLength, errorCode, message, splmMsg):
        # nDataLength – 1.0.0.1 버전 이후 사용하지 않음.
        # sErrorCode – 1.0.0.1 버전 이후 사용하지 않음.
        # sMessage – 1.0.0.1 버전 이후 사용하지 않음.
        # sSplmMsg - 1.0.0.1 버전 이후 사용하지 않음.
        self.q.put({
            "scrNo": scrNo,
            "sRQName": sRQName,
            "trCode": trCode,
            "recordName": recordName,
            "prevNext": prevNext
            # "dataLength": dataLength,
            # "errorCode" : errorCode,
            # "message" : message,
            # "splmMsg" : splmMsg
        })

    # 실시간 시세 이벤트
    def _OnReceiveRealData(self, jongmokCode, realType, realData):
        self.q.put({
            "jongmokCode": jongmokCode,
            "realType": realType,
            "realData": realData
        })

    # 수신 메시지 이벤트
    def _OnReceiveMsg(self, scrNo, sRQName, trCode, msg):
        self.q.put("receiveMsg.kiwoom", {
            "scrNo": scrNo,
            "sRQName": sRQName,
            "trCode": trCode,
            "msg": msg
        })

    # 체결데이터를 받은 시점을 알려준다.
    # sGubun – 0:주문체결통보, 1:잔고통보, 3:특이신호
    # sFidList – 데이터 구분은 ‘;’ 이다.
    def _OnReceiveChejanData(self, gubun, itemCnt, fidList):
        self.q.put({
            "gubun": gubun,
            "itemCnt": itemCnt,
            "fidList": fidList
        })

    # 통신 연결 상태 변경시 이벤트
    # code가 0이면 로그인 성공, 음수면 실패
    def _OnEventConnect(self, code):
        self.q.put(code)

    # 편입, 이탈 종목이 실시간으로 들어옵니다.
    # strCode : 종목코드
    # strType : 편입(“I”), 이탈(“D”)
    # strConditionName : 조건명
    # strConditionIndex : 조건명 인덱스
    def _OnReceiveRealCondition(self, code, type, conditionName, conditionIndex):
        self.q.put({
            "code": code,
            "type": type,
            "conditionName": conditionName,
            "conditionIndex": conditionIndex
        })

    # 조건검색 조회응답으로 종목리스트를 구분자(“;”)로 붙어서 받는 시점.
    # LPCTSTR sScrNo : 종목코드
    # LPCTSTR strCodeList : 종목리스트(“;”로 구분)
    # LPCTSTR strConditionName : 조건명
    # int nIndex : 조건명 인덱스
    # int nNext : 연속조회(2:연속조회, 0:연속조회없음)
    def _OnReceiveTrCondition(self, scrNo, codeList, conditionName, index, next):
        self.q.put({
            "scrNo": scrNo,
            "codeList": codeList,
            "conditionName": conditionName,
            "index": index,
            "next": next,
        })

    # 로컬에 사용자조건식 저장 성공여부 응답 이벤트
    def _OnReceiveConditionVer(self, ret, msg):
        self.q.put({
            "ret": ret,
            "msg": msg
        })

    ####################################################
    # Custom Methods
    ####################################################
    @staticmethod
    def quit():
        """ Quit the server """

        QApplication.quit()

    @staticmethod
    def parse_error_code(err_code):
        """
        Return the message of error codes

        :param err_code: Error Code
        :type err_code: str
        :return: Error Message
        """
        err_code = str(err_code)
        ht = {
            "0": "정상처리",
            "-100": "사용자정보교환에 실패하였습니다. 잠시후 다시 시작하여 주십시오.",
            "-101": "서버 접속 실패",
            "-102": "버전처리가 실패하였습니다.",
            "-200": "시세조회 과부하",
            "-201": "REQUEST_INPUT_st Failed",
            "-202": "요청 전문 작성 실패",
            "-300": "주문 입력값 오류",
            "-301": "계좌비밀번호를 입력하십시오.",
            "-302": "타인계좌는 사용할 수 없습니다.",
            "-303": "주문가격이 20억원을 초과합니다.",
            "-304": "주문가격은 50억원을 초과할 수 없습니다.",
            "-305": "주문수량이 총발행주수의 1%를 초과합니다.",
            "-306": "주문수량은 총발행주수의 3%를 초과할 수 없습니다."
        }
        return ht[err_code] + " (%s)" % err_code if err_code in ht else err_code


class KThread(threading.Thread):
    """
    Launch QT module as thread since QApplication.exec_ entering the event loop
    """

    def __init__(self, k_queue):
        super(KThread, self).__init__()
        self.k_queue = k_queue

    def run(self):
        app = QApplication(sys.argv)
        self.k_queue.put(Kiwoom(self.k_queue))
        app.exec_()


k_q = queue.Queue()
k_thread = KThread(k_q)
k_thread.start()

k_module = k_q.get()
