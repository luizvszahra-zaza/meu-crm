function doPost(e) {
  try {
    var params = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.openById(params.spreadsheet_id).getSheetByName(params.aba);
    var data = sheet.getDataRange().getValues();
    var headers = data[0].map(function(c) { return c.toString().toLowerCase().trim(); });
    
    // --- LÓGICA PARA A ABA CLIENTES ---
    if (params.aba === "clientes") {
      var colNomeIndex = headers.indexOf("nome");
      if (colNomeIndex === -1) colNomeIndex = 0;
      
      if (params.acao === "criar") {
        var novaLinhaCli = headers.map(function(h) {
          if (h === "nome") return params.novo_nome;
          if (h === "whatsapp" || h === "whats") return params.novo_whats;
          if (h === "endereco" || h === "endereço") return params.novo_end;
          if (h === "data") return Utilities.formatDate(new Date(), "GMT-3", "dd/MM/yyyy");
          return "";
        });
        sheet.appendRow(novaLinhaCli);
        return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
      } 
      else if (params.acao === "editar") {
        var linhaEditada = -1;
        for (var i = 1; i < data.length; i++) {
          if (data[i][colNomeIndex].toString().trim() === params.nome_original.trim()) {
            linhaEditada = i + 1;
            break;
          }
        }
        if (linhaEditada !== -1) {
          var idxWhats = headers.indexOf("whatsapp");
          if (idxWhats === -1) idxWhats = headers.indexOf("whats");
          var idxEnd = headers.indexOf("endereco");
          if (idxEnd === -1) idxEnd = headers.indexOf("endereço");
          
          sheet.getRange(linhaEditada, colNomeIndex + 1).setValue(params.novo_nome);
          if (idxWhats !== -1) sheet.getRange(linhaEditada, idxWhats + 1).setValue(params.novo_whats);
          if (idxEnd !== -1) sheet.getRange(linhaEditada, idxEnd + 1).setValue(params.novo_end);
          return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
        }
      }
      else if (params.acao === "deletar") {
        for (var i = 1; i < data.length; i++) {
          if (data[i][colNomeIndex].toString().trim() === params.nome_original.trim()) {
            sheet.deleteRow(i + 1);
            return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
          }
        }
      }
    }
    
    // --- LÓGICA PARA A ABA VISITAS ---
    if (params.aba === "visitas") {
      var colIdVIndex = headers.indexOf("id_v");
      if (colIdVIndex === -1) colIdVIndex = 0;
      
      if (params.acao === "criar") {
        var novoIdV = 1000;
        if (data.length > 1) {
          var maxId = 0;
          for (var i = 1; i < data.length; i++) {
            var val = parseInt(data[i][colIdVIndex]);
            if (!isNaN(val) && val > maxId) maxId = val;
          }
          novoIdV = maxId + 1;
        }
        var novaLinha = headers.map(function(h) {
          if (h === "id_v") return novoIdV.toString();
          if (h === "cliente") return params.cliente;
          if (h === "data") return params.data;
          if (h === "hora") return params.hora;
          if (h === "endereco" || h === "endereço") return params.endereco;
          return "";
        });
        sheet.appendRow(novaLinha);
        return ContentService.createTextOutput(JSON.stringify({"status": "sucesso", "id_v": novoIdV})).setMimeType(ContentService.MimeType.JSON);
      } 
      else if (params.acao === "editar") {
        var linhaVisita = -1;
        for (var i = 1; i < data.length; i++) {
          if (data[i][colIdVIndex].toString().trim() === params.id_v.trim()) {
            linhaVisita = i + 1;
            break;
          }
        }
        if (linhaVisita !== -1) {
          var idxCli = headers.indexOf("cliente");
          var idxDt = headers.indexOf("data");
          var idxHr = headers.indexOf("hora");
          var idxEndV = headers.indexOf("endereco");
          if (idxEndV === -1) idxEndV = headers.indexOf("endereço");
          
          if (idxCli !== -1) sheet.getRange(linhaVisita, idxCli + 1).setValue(params.cliente);
          if (idxDt !== -1) sheet.getRange(linhaVisita, idxDt + 1).setValue(params.data);
          if (idxHr !== -1) sheet.getRange(linhaVisita, idxHr + 1).setValue(params.hora);
          if (idxEndV !== -1) sheet.getRange(linhaVisita, idxEndV + 1).setValue(params.endereco);
          return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
        }
      }
      else if (params.acao === "deletar") {
        for (var i = 1; i < data.length; i++) {
          if (data[i][colIdVIndex].toString().trim() === params.id_v.trim()) {
            sheet.deleteRow(i + 1);
            return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
          }
        }
      }
    }
    
    // --- LÓGICA PARA A ABA ORÇAMENTOS ---
    if (params.aba === "orcamentos") {
      var colIdIndex = headers.indexOf("id");
      if (colIdIndex === -1) colIdIndex = 0;
      var colStatusIndex = headers.indexOf("status");
      
      var linhaOrc = -1;
      for (var i = 1; i < data.length; i++) {
        if (data[i][colIdIndex].toString().trim() === params.id.trim()) {
          linhaOrc = i + 1;
          break;
        }
      }
      if (linhaOrc !== -1 && colStatusIndex !== -1) {
        sheet.getRange(linhaOrc, colStatusIndex + 1).setValue(params.novo_status);
        return ContentService.createTextOutput(JSON.stringify({"status": "sucesso"})).setMimeType(ContentService.MimeType.JSON);
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({"status": "nao encontrado"})).setMimeType(ContentService.MimeType.JSON);
  } catch(error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "erro", "motivo": error.toString()})).setMimeType(ContentService.MimeType.JSON);
  }
}
