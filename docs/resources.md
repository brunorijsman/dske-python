[Back to main page](/dske-python/)

# Resources

### IETF draft draft-mwag-dske

The following Internet Engineering Task Force (IETF) Internet-Draft describes the DSKE protocol
that was the inspiration for the implementation in this repository:

ID: draft-mwag-dske <br/>
Title: Distributed Symmetric Key Establishment (DSKE) <br/>
Authors: Mattia Montagna, Manfred von Willich, Melchior Aelmans, Gert Grammel <br/>
Link: [https://datatracker.ietf.org/doc/draft-mwag-dske/](https://datatracker.ietf.org/doc/draft-mwag-dske/) <br/>

### ArXiv paper Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system

The following arXiv paper describes the DSKE protocol in more detail:

ID: arXiv:2205.00615 <br/>
Title: Distributed Symmetric Key Establishment: A scalable, quantum-proof key distribution system <br/>
Authors: Hoi-Kwong Lo, Mattia Montagna, Manfred von Willich<br/>
Link: [https://arxiv.org/abs/2205.00615](https://arxiv.org/abs/2205.00615) <br/>

### ArXiv paper Composable Security of Distributed Symmetric Key Establishment Protocol

The following arXiv paper provides a security proof for the DSKE protocol:

ID: arXiv:2304.13789 <br/>
Title: Composable Security of Distributed Symmetric Key Establishment Protocol <br/>
Authors: Jie Lin, Manfred von Willich, Hoi-Kwong Lo <br/>
Link: [https://arxiv.org/abs/2304.13789](https://arxiv.org/abs/2304.13789) <br/>

### Company Quantum Bridge

Quantum Bridge is the company that published the above draft and papers and that sells a commercial
implementation of the DSKE protocol.
This open source implementation has been developed completely independently of and without any
involvement of Quantum Bridge.

Company name: Quantum Bridge <br/>
Link: [https://qubridge.io/](https://qubridge.io/) <br/>

### Paper A Secret Key Spreading Protocol for Extending ETSI Quantum Key Distribution

The following paper describes a similar protocol for relaying QKD keys using Shamir's Secret
Sharing (SSS):

Title: A Secret Key Spreading Protocol for Extending ETSI Quantum Key Distribution <br/>
Authors: Thomas Prévost, Bruno Martin, Olivier Alibart <br/>
Link: [https://www.scitepress.org/Papers/2025/130771/130771.pdf](https://www.scitepress.org/Papers/2025/130771/130771.pdf) <br/>

### Key delivery standard ETSI GS QKD 014

The code contains a simplified implementation of the key delivery interface defined in the
following standard:

ID: ETSI GS QKD 014 V1.1.1 (2019-02) <br/>
Title: Quantum Key Distribution (QKD); Protocol and data format of REST-based key delivery API <br/>
Link: [https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/014/01.01.01_60/gs_qkd014v010101p.pdf) <br/>

### Cloud-based ETSI GS QKD 014 service QuKayDee

For a fully standards-compliant cloud-hosted implementation of the ETSI GS QKD 014 key delivery 
interface see:

Title: QuKayDee: A QKD network simulator, focused on APIs <br/>
Authors: Bruno Rijsman <br/>
Link: [https://qukaydee.com/pages/about](https://qukaydee.com/pages/about) <br/>

### Self-hosted ETSI GS QKD 014 service qkd_kme_server

For a self-hosted implementation of the ETSI GS QKD 014 interface see:

Title: ETSI-compliant Quantum Key Distribution (QKD) Key Management Entity server <br/>
Authors: Thomas Prévost <br/>
Link: [https://github.com/thomasarmel/qkd_kme_server](https://github.com/thomasarmel/qkd_kme_server) <br/>
