package br.ma.ecochatbot.resource;

import br.ma.ecochatbot.dto.MensagemMenuDTO;
import br.ma.ecochatbot.dto.MensagemResponse;
import br.ma.ecochatbot.service.MensagemService;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/mensagem")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class MensagemResource {

    @Inject
    MensagemService mensagemService;

    @POST
    @Path("/menuEnviar")
    public Response enviarMenu(MensagemMenuDTO dto) {
        MensagemResponse resposta = mensagemService.enviarMenu(dto);
        int statusCode = resposta.codigo() == 1 ? 200 : 400;
        return Response.status(statusCode).entity(resposta).build();
    }
}
