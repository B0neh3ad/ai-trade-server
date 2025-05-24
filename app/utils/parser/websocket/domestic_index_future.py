from dataclasses import dataclass

### 국내 지수선물 ###

### 실시간호가 (H0IFASP0) ###
@dataclass
class DomesticIndexFutureOrderbookResponse:
    futs_shrn_iscd: str    #선물 단축 종목코드
    bsop_hour: str    #영업 시간
    futs_askp1: str    #선물 매도호가1
    futs_askp2: str    #선물 매도호가2
    futs_askp3: str    #선물 매도호가3
    futs_askp4: str    #선물 매도호가4
    futs_askp5: str    #선물 매도호가5
    futs_bidp1: str    #선물 매수호가1
    futs_bidp2: str    #선물 매수호가2
    futs_bidp3: str    #선물 매수호가3
    futs_bidp4: str    #선물 매수호가4
    futs_bidp5: str    #선물 매수호가5
    askp_csnu1: str    #매도호가 건수1
    askp_csnu2: str    #매도호가 건수2
    askp_csnu3: str    #매도호가 건수3
    askp_csnu4: str    #매도호가 건수4
    askp_csnu5: str    #매도호가 건수5
    bidp_csnu1: str    #매수호가 건수1
    bidp_csnu2: str    #매수호가 건수2
    bidp_csnu3: str    #매수호가 건수3
    bidp_csnu4: str    #매수호가 건수4
    bidp_csnu5: str    #매수호가 건수5
    askp_rsqn1: str    #매도호가 잔량1
    askp_rsqn2: str    #매도호가 잔량2
    askp_rsqn3: str    #매도호가 잔량3
    askp_rsqn4: str    #매도호가 잔량4
    askp_rsqn5: str    #매도호가 잔량5
    bidp_rsqn1: str    #매수호가 잔량1
    bidp_rsqn2: str    #매수호가 잔량2
    bidp_rsqn3: str    #매수호가 잔량3
    bidp_rsqn4: str    #매수호가 잔량4
    bidp_rsqn5: str    #매수호가 잔량5
    total_askp_csnu: str    #총 매도호가 건수
    total_bidp_csnu: str    #총 매수호가 건수
    total_askp_rsqn: str    #총 매도호가 잔량
    total_bidp_rsqn: str    #총 매수호가 잔량
    total_askp_rsqn_icdc: str    #총 매도호가 잔량 증감
    total_bidp_rsqn_icdc: str    #총 매수호가 잔량 증감

### 실시간체결가 (H0IFCNT0) ###
@dataclass
class DomesticIndexFutureExecutionResponse:
    futs_shrn_iscd: str    #선물 단축 종목코드
    bsop_hour: str    #영업 시간
    futs_prdy_vrss: str    #선물 전일 대비
    prdy_vrss_sign: str    #전일 대비 부호
    futs_prdy_ctrt: str    #선물 전일 대비율
    futs_prpr: str    #선물 현재가
    futs_oprc: str    #선물 시가2
    futs_hgpr: str    #선물 최고가
    futs_lwpr: str    #선물 최저가
    last_cnqn: str    #최종 거래량
    acml_vol: str    #누적 거래량
    acml_tr_pbmn: str    #누적 거래 대금
    hts_thpr: str    #HTS 이론가
    mrkt_basis: str    #시장 베이시스
    dprt: str    #괴리율
    nmsc_fctn_stpl_prc: str    #근월물 약정가
    fmsc_fctn_stpl_prc: str    #원월물 약정가
    spead_prc: str    #스프레드1
    hts_otst_stpl_qty: str    #HTS 미결제 약정 수량
    otst_stpl_qty_icdc: str    #미결제 약정 수량 증감
    oprc_hour: str    #시가 시간
    oprc_vrss_prpr_sign: str    #시가2 대비 현재가 부호
    oprc_vrss_nmix_prpr: str    #시가 대비 지수 현재가
    hgpr_hour: str    #최고가 시간
    hgpr_vrss_prpr_sign: str    #최고가 대비 현재가 부호
    hgpr_vrss_nmix_prpr: str    #최고가 대비 지수 현재가
    lwpr_hour: str    #최저가 시간
    lwpr_vrss_prpr_sign: str    #최저가 대비 현재가 부호
    lwpr_vrss_nmix_prpr: str    #최저가 대비 지수 현재가
    shnu_rate: str    #매수2 비율
    cttr: str    #체결강도
    esdg: str    #괴리도
    otst_stpl_rgbf_qty_icdc: str    #미결제 약정 직전 수량 증감
    thpr_basis: str    #이론 베이시스
    futs_askp1: str    #선물 매도호가1
    futs_bidp1: str    #선물 매수호가1
    askp_rsqn1: str    #매도호가 잔량1
    bidp_rsqn1: str    #매수호가 잔량1
    seln_cntg_csnu: str    #매도 체결 건수
    shnu_cntg_csnu: str    #매수 체결 건수
    ntby_cntg_csnu: str    #순매수 체결 건수
    seln_cntg_smtn: str    #총 매도 수량
    shnu_cntg_smtn: str    #총 매수 수량
    total_askp_rsqn: str    #총 매도호가 잔량
    total_bidp_rsqn: str    #총 매수호가 잔량
    prdy_vol_vrss_acml_vol_rate: str    #전일 거래량 대비 등락율
    dscs_bltr_acml_qty: str    #협의 대량 거래량
    dynm_mxpr: str    #실시간상한가
    dynm_llam: str    #실시간하한가
    dynm_prc_limt_yn: str    #실시간가격제한구분

### 실시간체결통보 (H0IFCNI0, H0IFCNI9) ###
@dataclass
class DomesticIndexFutureNoticeResponse:
    cust_id: str    #고객ID
    acnt_no: str    #계좌번호
    oder_no: str    #주문번호
    ooder_no: str    #원주문번호
    seln_byov_cls: str    #매도매수구분
    rctf_cls: str    #정정구분
    oder_kind2: str    #주문종류2
    futs_shrn_iscd: str    #선물 단축 종목코드
    cntg_qty: str    #체결 수량
    cntg_unpr: str    #체결단가
    futs_cntg_hour: str    #선물 체결 시간
    rfus_yn: str    #거부여부
    cntg_yn: str    #체결여부
    acpt_yn: str    #접수여부
    brnc_no: str    #지점번호
    oder_qty: str    #주문수량
    acnt_name: str    #계좌명
    cntg_isnm: str    #체결종목명
    oder_cond: str    #주문조건
    ord_grp: str    #주문그룹ID
    ord_grpseq: str    #주문그룹SEQ
    order_prc: str    #주문가격