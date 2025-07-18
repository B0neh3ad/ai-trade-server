
from dataclasses import dataclass

@dataclass
class ResponseBodyoutput1:
    hts_kor_isnm: str    #HTS 한글 종목명
    futs_prpr: str    #선물 현재가
    futs_prdy_vrss: str    #선물 전일 대비
    prdy_vrss_sign: str    #전일 대비 부호
    futs_prdy_clpr: str    #선물 전일 종가
    futs_prdy_ctrt: str    #선물 전일 대비율
    acml_vol: str    #누적 거래량
    acml_tr_pbmn: str    #누적 거래 대금
    hts_otst_stpl_qty: str    #HTS 미결제 약정 수량
    otst_stpl_qty_icdc: str    #미결제 약정 수량 증감
    futs_oprc: str    #선물 시가2
    futs_hgpr: str    #선물 최고가
    futs_lwpr: str    #선물 최저가
    futs_mxpr: str    #선물 상한가
    futs_llam: str    #선물 하한가
    basis: str    #베이시스
    futs_sdpr: str    #선물 기준가
    hts_thpr: str    #HTS 이론가
    dprt: str    #괴리율
    crbr_aply_mxpr: str    #서킷브레이커 적용 상한가
    crbr_aply_llam: str    #서킷브레이커 적용 하한가
    futs_last_tr_date: str    #선물 최종 거래 일자
    hts_rmnn_dynu: str    #HTS 잔존 일수
    futs_lstn_medm_hgpr: str    #선물 상장 중 최고가
    futs_lstn_medm_lwpr: str    #선물 상장 중 최저가
    delta_val: str    #델타 값
    gama: str    #감마
    theta: str    #세타
    vega: str    #베가
    rho: str    #로우
    hist_vltl: str    #역사적 변동성
    hts_ints_vltl: str    #HTS 내재 변동성
    mrkt_basis: str    #시장 베이시스
    acpr: str    #행사가

@dataclass
class ResponseBodyoutput2:
    bstp_cls_code: str    #업종 구분 코드
    hts_kor_isnm: str    #HTS 한글 종목명
    bstp_nmix_prpr: str    #업종 지수 현재가
    prdy_vrss_sign: str    #전일 대비 부호
    bstp_nmix_prdy_vrss: str    #업종 지수 전일 대비
    bstp_nmix_prdy_ctrt: str    #업종 지수 전일 대비율

@dataclass
class ResponseBodyoutput3:
    bstp_cls_code: str    #업종 구분 코드
    hts_kor_isnm: str    #HTS 한글 종목명
    bstp_nmix_prpr: str    #업종 지수 현재가
    prdy_vrss_sign: str    #전일 대비 부호
    bstp_nmix_prdy_vrss: str    #업종 지수 전일 대비
    bstp_nmix_prdy_ctrt: str    #업종 지수 전일 대비율

@dataclass
class DomesticFutureoptionPriceResponse:
    rt_cd: str    #성공 실패 여부
    msg_cd: str    #응답코드
    msg1: str    #응답메세지
    output1: ResponseBodyoutput1    #응답상세1
    output2: ResponseBodyoutput2    #응답상세2
    output3: ResponseBodyoutput3    #응답상세3
